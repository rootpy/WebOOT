import os

__version__ = "0.1"

from commands import getstatusoutput
from os.path import abspath, dirname, exists, join as pjoin
from setuptools import setup, find_packages

here = abspath(dirname(__file__))
README = open(pjoin(here, 'README.txt')).read()
CHANGES = open(pjoin(here, 'CHANGES.txt')).read()

requires = [
    # Basic requirements
    'pyramid',
    'pyramid_debugtoolbar',
    'waitress',
    
    'Paste',
    'PasteScript',
    'PasteDeploy',
    'WebError',

    # File mimetype detection
    'filemagic',
    
    # Database
    # 'pymongo',
    # Used to run mongo and determine when it started
    # 'pexpect',

    #Markdown format rendering
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
    )

