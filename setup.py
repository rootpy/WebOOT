import os

from commands import getstatusoutput
from os.path import abspath, dirname, exists, join as pjoin
from setuptools import setup, find_packages

here = abspath(dirname(__file__))
README = open(pjoin(here, 'README.txt')).read()
CHANGES = open(pjoin(here, 'CHANGES.txt')).read()
version_path = pjoin(here, "weboot", "version.txt")

try:
    import dulwich
except ImportError:
    if exists(version_path):
        __version__ = open(version_path).read().strip()
    else:
        __version__ = "__UNKNOWN__"
else:
    repo = dulwich.repo.Repo(here)
    refs = repo.refs
    branch = sha = refs.read_ref("HEAD")
    
    if branch.startswith("ref:"):
        sha = refs.as_dict()["HEAD"]
        _, _, branch = branch.rpartition("/")
    else:
        branch = "_unk"
    
    __version__ = "{0}-{1}".format(branch, sha[:6])
    
    # No `with` to be <2.5 safe
    fd = open(version_path, "w")
    fd.write(__version__)
    fd.close()        

requires = [
    # Basic requirements
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    
    'PasteDeploy',
    
    # Database
    'pymongo',
    # Used to run mongo and determine when it started
    'pexpect',
    # OpenAuth (currently unused
    # 'velruse', 
    # Used to host HTTPs servers
    # 'pyOpenSSL',
    
    # Markdown format rendering
    'markdown',
]

setup(
    name='WebOOT',
    version=__version__,
    description='WebOOT',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Peter Waller',
    author_email='peter.waller@cern.ch',
    url='https://weboot.cern.ch',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    test_suite="weboot",
    package_data={
        "weboot" : ["version.txt"],
    },
    entry_points = """
        [paste.app_factory]
        main = weboot:main
    """,
    paster_plugins=['pyramid'],
    )

