WebOOT

The web ROOT viewer.

Prerequisite:

If this works, then weboot should work:

    $ python -c "import ROOT"

Installation:

Using virtualenv you can install all dependencies
in the current directory:

./virtualenv.py --distribute env
env/bin/pip install -e .
paster serve --reload development.ini