"""
"""

from contextlib import contextmanager
from random import randint
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from thread import get_ident

import ROOT as R

from pyramid.response import Response

from .. import log; log = log[__name__]
from ...utils.timer import timer

        
