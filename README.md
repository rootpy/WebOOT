WebOOT
------

A web ROOT viewer.

Fed up with writing plot scripts?

# Introduction

WebOOT aims to make it easy to make navigate between ROOT files and do advanced
maniuplation on many plots simultaneously.

The first idea is that all plots should be addressable at a URL.

# Prerequisites

If these work, then weboot should work:

    $ python -c "import ROOT"
    $ convert -h
    (from ImageMagick)

# Installation

Using virtualenv you can install all dependencies
in the current directory:

    git clone git://github.com/rootpy/WebOOT
    python WebOOT/setup.py develop --user
    mkdir results/
    # Copy some histograms to your results/ directory, then run..
    pserve --reload WebOOT/development.ini

Please see `CONTRIBUTING`.

