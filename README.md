[![Build Status](https://travis-ci.org/rootpy/WebOOT.png)](https://travis-ci.org/rootpy/WebOOT)

WebOOT
------

WebOOT is a [ROOT](http://root.cern.ch/) viewer for the web.

Fed up with writing plot scripts?

## Introduction

WebOOT aims to make it easy to make navigate between ROOT files and do advanced
manipulation on many plots simultaneously.

The first idea is that all plots should be addressable at a URL.

See the presentation at the
[ROOT Users Workshop 2013](http://indico.cern.ch/conferenceDisplay.py?confId=217511):
[Abstract](http://indico.cern.ch/contributionDisplay.py?contribId=50&confId=217511), 
[PDF](http://indico.cern.ch/getFile.py/access?contribId=50&resId=0&materialId=slides&confId=217511)

## Links

* Website: https://github.com/rootpy/WebOOT
* Documentation: https://weboot.readthedocs.org/
* Mailing list: [send email](mailto:weboot-users@cern.ch),
or [subscribe](https://e-groups.cern.ch/e-groups/EgroupsSubscription.do?egroupName=weboot-users).

## Prerequisites

To make WebOOT work, you need
[PyROOT](http://root.cern.ch/drupal/content/pyroot),
[ImageMagick](http://www.imagemagick.org/),
[pexpect](https://pypi.python.org/pypi/pexpect/) and
[filemagic](https://pypi.python.org/pypi/filemagic/).

Copy & paste these commands into a shell to check:

    $ python -c "import ROOT"
    $ convert -h
    $ python -c "import magic"

## Installation

This is a simple way to install WebOOT:

    git clone git://github.com/rootpy/WebOOT
    cd WebOOT/
    python setup.py develop --user


## Usage

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

Please see [CONTRIBUTING](https://github.com/rootpy/WebOOT/blob/master/CONTRIBUTING)

