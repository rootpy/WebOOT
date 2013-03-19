WebOOT
------

A web ROOT viewer.

Fed up with writing plot scripts?

# Introduction

WebOOT aims to make it easy to make navigate between ROOT files and do advanced
manipulation on many plots simultaneously.

The first idea is that all plots should be addressable at a URL.

# Prerequisites

To make WebOOT work, you need
[PyROOT](http://root.cern.ch/drupal/content/pyroot),
[ImageMagick](http://www.imagemagick.org/),
[pexpect](https://pypi.python.org/pypi/pexpect/) and
[filemagic](https://pypi.python.org/pypi/filemagic/).

Copy & paste these commands into a shell to check:

    $ python -c "import ROOT"
    $ convert -h
    $ python -c "import magic"

# Installation

This is a simple way to install WebOOT:

    git clone git://github.com/rootpy/WebOOT
    cd WebOOT/
    python setup.py develop --user

Extra Python package dependencies that WebOOT uses and you don't have already
will be fetched and installed from [PyPI](https://pypi.python.org/pypi/) automatically:
[rootpy](https://pypi.python.org/pypi/rootpy/)
[pyramid](https://pypi.python.org/pypi/pyramid/),
[pyramid_debugtoolbar](https://pypi.python.org/pypi/pyramid_debugtoolbar/),
[waitress](https://pypi.python.org/pypi/waitress/),
[Paste](https://pypi.python.org/pypi/Paste/),
[PasteScript](https://pypi.python.org/pypi/PasteScript/),
[PasteDeploy](https://pypi.python.org/pypi/PasteDeploy/),
[WebError](https://pypi.python.org/pypi/WebError/).

# Usage

If you downloaded WebOOT to `Folder_A` and want to browse your ROOT files in `Folder_B`,
open a terminal and type

    $ cd Folder_A
    $ pserve --reload Folder_B/development.ini

You will get a message on your screen that looks like this:

	Starting subprocess with file monitor
	Starting server in PID 31840.
	serving on http://0.0.0.0:6543

Copy & paste the URL into the web browser of your choice and follow the `browse` link
( or go directly to http://0.0.0.0:6543/browse/ ).

Please see `CONTRIBUTING`.

