from .rootfile import RootFileTraverser


class TObjArrayTraverser(RootFileTraverser):
    
    def __init__(self, request, obj_array):
        super(TObjArrayTraverser, self).__init__(request, obj_array)
        mapping = self.mapping = {}
        for i, item in enumerate(obj_array):
            orig_name = name = item.GetName()
            n = 0
            while name in mapping:
                name = "{0};{1}".format(orig_name, n)
                n += 1
            mapping[name] = i                    
    
    @property
    def path(self):
        return self.__name__
    
    @property
    def items(self):
        keys = [self[k.GetName()] for k in list(self.rootfile)]
        keys.sort(key=lambda k: k.name)
        return keys
    
    def __getitem__(self, subpath):
        if subpath not in self.mapping:
            return
        root_obj = self.rootfile.At(self.mapping[subpath])
        return RootObject.from_parent(self, subpath, root_obj)
