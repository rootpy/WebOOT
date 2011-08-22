from os import listdir
from os.path import basename, exists, isfile, isdir, join as pjoin

import re
import fnmatch

from pyramid.httpexceptions import HTTPError, HTTPFound, HTTPNotFound, HTTPMethodNotAllowed
from pyramid.traversal import traverse, resource_path
from pyramid.url import static_url

import ROOT as R

from ..locationaware import LocationAware




