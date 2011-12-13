from .. import log; log = log.getChild("vfs")

import os
import time
from threading import Lock, Thread

import ROOT as R

"""
RootVFS

Interface to a cached tree with root files
Objects are accessed by the following convention:

/my/path/to/file.root/subpath/object

A RootVFS is initialized with a jail path, outside of which no access
is allowed.

The only interface function is __getitem__, which returns an object which has
the following functions: 
    isdir() == True for directories and files which allow recursion
    infile() == True if the directory is inside a vfile
    isvfile() == True only for files which allow recursion
    isobject() == True only for objects inside files
    listdir() returns a listing of this directory (exists if isdir() == True)
    get() returns the root object (exists if isobject() == True)

"""

directory_ls_timeout = 2 #seconds
root_file_validate_timeout = 2 #seconds
root_file_close_timeout = 30 #seconds


def get_key_class(key):
    if not isinstance(key, R.TKey):
        return type(key)
    class_name = key.GetClassName()
    try:
        class_object = getattr(R, class_name)
        return class_object
    except AttributeError:
        return None
class VFSDirectory(object):
    isdir = lambda self : True
    infile = isvfile = isobject = lambda self : False

    def valid(self):
        return os.path.exists(self._dir)

    def __init__(self, _dir, _vfs):
        self._dir = _dir
        self._listing = []
        self._ltime = 0
        self._vfs = _vfs

    def listdir(self):
        now = time.time()
        if now - self._ltime > directory_ls_timeout:
            self._listing = os.listdir(self._dir)
        return self._listing

    def __getitem__(self, k):
        return self._vfs[os.path.join(self._dir, k)]

    def __str__(self):
        return self._dir

class VFSFile(object):
    isdir = infile = isvfile = isobject = lambda self : False

    def valid(self):
        return os.path.exists(self._dir)

    def __init__(self, _dir):
        self._dir = _dir

    def __str__(self):
        return self._dir

class VFSRootDirectory(object):
    isdir = infile = lambda self : True
    isobject = lambda self : False

    def valid(self):
        return self._rcf.valid

    def __init__(self, _rcf, _dir, _dict):
        """
        rcf = root cache file
        dir = directory inside root cache file
        dict = dictionary of entries 
        """
        self._rcf = _rcf
        self._dir = _dir
        self._dict = _dict

    def isvfile(self):
        return not self._dir

    def listdir(self):
        return self._dict.keys()

    def __getitem__(self, k):
        res = self._dict[k]
        if isinstance(res, dict):
            sd = os.path.join(self._dir, k)
            return VFSRootDirectory(self._rcf, sd, res)
        return VFSRootObject(self._rcf, res)

    def __str__(self):
        return os.path.join(str(self._rcf), self._dir)


class VFSRootObject(object):
    isobject = infile = lambda self : True
    isdir = isvfile = lambda self : False

    def valid(self):
        return self._rcf.valid

    def __init__(self, _rcf, _ref):
        self._rcf = _rcf
        self._ref = _ref
        self.name = _ref.name()
        self.class_name = _ref.class_name
        self.info = _ref.info

    def get(self):
        log.warning("VFS Root get of %s"%self.name)
        rf = self._rcf.root_file
        return self._ref.get_from(rf)

class AccessDeniedException(Exception):
    pass

class RootVFS(object):
    def __init__(self, chroot_jail="/"):
        self.chroot_jail = os.path.realpath(chroot_jail)
        self.recent = {}
        self.cache = RootCache() # singleton accessor

    def __getitem__(self, name):
        rq = self.recent.get(name, None)
        if rq and rq.valid():
            return rq
        root_file, subdir = self.rvfs_split(name)
        if not root_file:
            if not os.path.exists(name):
                raise KeyError("Unknown path: %s" % name)
            res = VFSDirectory(name, self)
        else:
            rfc = self.cache[root_file]
            if not rfc:
                res = VFSFile(root_file)
            else:
                sdc = rfc.entries_flat.get(subdir, None)
                if not sdc:
                    raise KeyError("Unknown path %s in file %s" % (subdir, root_file))
                if isinstance(sdc, dict):
                    res = VFSRootDirectory(rfc, subdir, sdc)
                else:
                    res = VFSRootObject(rfc, sdc)
        self.recent[name] = res
        return res

    def get(self, path):
        try:
            res = self[path]
        except KeyError:
            return
        return res

    def rvfs_split(self, dir):
        rp = os.path.realpath(dir)
        if not os.path.realpath(dir).startswith(self.chroot_jail):
            raise AccessDeniedException("Access to '%s' from jail '%s' denied!"
                    % (dir, self.chroot_jail))
        np = os.path.normpath(dir)
        current_end = len(np)
        while current_end > 0:
            if os.path.isfile(np[:current_end]):
                return np[:current_end], np[current_end+1:]
            current_end = np.rfind(os.path.sep, 0, current_end)
        return None, None

def extract_axis_info(axis):
    info = {}
    info["title"] = axis.GetTitle()
    info["n_bins"] = axis.GetNbins()
    info["max"] = axis.GetXmax()
    info["min"] = axis.GetXmin()
    bins_arr = axis.GetXbins()
    if bins_arr.GetSize() > 0:
        info["bins"] = [bins_arr.At(i) for i in xrange(bins_arr.GetSize())]
    labels = axis.GetLabels()
    if labels:
        info["labels"] = list(labels)
    return info

def extract_info(obj):
    info = {}
    info["title"] = obj.GetTitle()
    if isinstance(obj, R.TH1):
        info["dimension"] = obj.GetDimension()
        info["entries"] = obj.GetEntries()
        info["maximum"] = obj.GetMaximum()
        info["minimum"] = obj.GetMinimum()
        info["maximum_bin"] = obj.GetMaximumBin()
        info["minimum_bin"] = obj.GetMinimumBin()
        info["mean"] = obj.GetMean()
        info["mean_error"] = obj.GetMeanError()
        info["rms"] = obj.GetRMS()
        info["rms_error"] = obj.GetRMSError()
        info["x"] = extract_axis_info(obj.GetXaxis())
        if obj.GetDimension() > 1:
            info["y"] = extract_axis_info(obj.GetYaxis())
            if obj.GetDimension() > 2:
                info["z"] = extract_axis_info(obj.GetZaxis())
    return info

class RootObjectRef(object):
    def get_from(self, root_file):
        return root_file
    def add(self, subdir):
        return SimpleObjectRef(subdir)
    def name(self):
        return os.path.basename(self.name)


class SimpleObjectRef(object):
    def __init__(self, name):
        self.dir = name

    def get_from(self, root_file):
        return root_file.Get(self.dir)

    def add(self, subdir):
        return SimpleObjectRef(os.path.join(self.dir, subdir))

    def add_objarray(self, subdir, name):
        return NestedObjectRef((('G', self.dir), ('O', subdir, name)))

    def name(self):
        return os.path.basename(self.dir)

class NestedObjectRef(object):
    """ Access Tuple format: (('G', objarray_name), ('O', <index>, name), ('G',hist))
        G for Get, O for TObjArray
    """
    def __init__(self, access_tuple):
        self.access_tuple = access_tuple

    def get_from(self, root_file):
        current = root_file
        for v in self.access_tuple:
            if not current:
                return
            if v[0] == 'G':
                current = current.Get(v[1])
            elif v[0] == 'O':
                current = current.At(v[1])
            else:
                raise RuntimeError("Invalid NestedRootCacheObject tuple entry: %s" % str(v))
        return current

    def add(self, subdir):
        return NestedObjectRef(self.access_tuple + ('G', subdir))

    def add_objarray(self, index, name):
        return NestedObjectRef(self.access_tuple + ('O', index, name))

    def name(self):
        return os.path.basename(self.access_tuple[-1][-1])

class RootCacheFile(object):
    _open_root_files_lock = Lock()
    _open_root_files = set()

    def __init__(self, name, realname):
        self._valid, self._exists = True, True
        self.lock = Lock()
        self.tfile, self.otime, self.atime = None, None, None
        self.vtime = 0
        self.name, self.realname = name, realname
        try:
            self.mtime = os.path.getmtime(realname)
        except OSError:
            self._exists = self._valid = False
        self.validate()
        now = time.time()
        self.entries_flat = {}
        if self.root_file:
            self.entries = self.root_listing()
        self.entries_flat[""] = self.entries
        later = time.time()
        log.warning("Read %i entries in %.4f seconds"  % (len(self.entries_flat), (later-now)))

    @property
    def exists(self):
        self.validate()
        return self._exists

    @property
    def valid(self):
        self.validate()
        return self._valid

    @property
    def root_file(self):
        with self.lock:
            if self.tfile:
                self.atime = time.time()
                return self.tfile
            self.tfile = R.TFile.Open(self.realname)
            if not self.tfile:
                return
            with self._open_root_files_lock:
                self._open_root_files.add(self)
            self.otime = self.atime = time.time()
            ## scan file
            return self.tfile

    @classmethod
    def maintenance(obj):
        with obj._open_root_files_lock:
            for f in obj._open_root_files:
                f.close_timeout()
        # This closes the files
        import gc
        gc.collect()

    def close_timeout(self):
        if self.tfile:
            if self.atime - self.otime > root_file_close_timeout:
                self.close()

    def close(self):
        self.tfile = self.otime = self.atime = None
        with self._open_root_files_lock:
            self._open_root_files.remove(self)

    def validate(self):
        if not self._valid:
            return False
        # only validate every second max
        now = time.time()
        if now - self.vtime < root_file_validate_timeout:
            return True

        try:
            if not os.path.samefile(self.name, self.realname):
                self._valid = False
                return False
            mtime = os.path.getmtime(self.realname)
            if mtime != mtime:
                self._valid = False
        except OSError:
            self._exists = self._valid = False
        self.vtime = now
        return self._valid

    def root_listing(self, dir_ref=RootObjectRef(), dir_name="", key=None):
        o = None
        if key:
            cls = get_key_class(key)
        else:
            o = dir_ref.get_from(self.root_file)
            cls = o.__class__
            
        if issubclass(cls, R.TDirectory):
            o = o or dir_ref.get_from(self.root_file)
            entries = {}
            for key in o.GetListOfKeys():
                name = key.GetName()
                absname = os.path.join(dir_name, name)
                entries[name] = self.root_listing(dir_ref.add(name), absname, key=key)
                self.entries_flat[absname] = entries[name]
            return entries            
        elif issubclass(cls, R.TObjArray):
            o = o or dir_ref.get_from(self.root_file)
            entries = {}
            for i, item in enumerate(o):
                orig_name = name = item.GetName()
                n = 0
                while name in entries.keys():
                    name = "{0};{1}".format(orig_name, n)
                    n += 1
                absname = os.path.join(dir_name, name)
                entries[name] = self.root_listing(dir_ref.add_objarray(i, name), absname, key=key)
                self.entries_flat[absname] = entries[name]
            return entries
        else:
            dir_ref.class_name = cls.__name__
            dir_ref.info = {} # extract_info(o)
            self.entries_flat[dir_name] = dir_ref
            return dir_ref


"""
RootCache
Singleton Threadsafe Cache that provides Root File Contents and TFile objects
The cache of an inidvidual Root file is flushed on mtime changes
"""

class RootCache(object):
    """
    A cache mapping a file name to a CacheEntry
    Both the relative and the real file name (symlinks, etc) is checked.
    """
    file_cache = {}
    lock = Lock()
    def __getitem__(_dummy_, name):
        realname = os.path.realpath(name)
        with RootCache.lock:
            result = RootCache.file_cache.get(name, None)
            if result is None or not result.valid:
                log.warning("refreshing rootcache for file %s"%name)
                result = RootCacheFile(name, realname)
                if result.root_file:
                    RootCache.file_cache[name] = result
                else:
                    result = None
        return result

rc = RootCache()
#f = rc["data.root"]

def maintenance_main():
    while True:
        time.sleep(15)
        RootCacheFile.maintenance()
maintenance_thread = Thread()
maintenance_thread.run = maintenance_main
maintenance_thread.start()
