WebOOT

The web ROOT viewer.

Fed up with writing plot scripts?

Prerequisite:

If these work, then weboot should work:

    $ python -c "import ROOT"
    $ convert -h
    (from ImageMagick)

Installation:

Using virtualenv you can install all dependencies
in the current directory:

    ./virtualenv.py --distribute env
    env/bin/pip install -e .
    mkdir results/
    # Copy some histograms to your results/ directory, then run..
    env/bin/paster serve --reload development.ini

Please see `CONTRIBUTING`.
