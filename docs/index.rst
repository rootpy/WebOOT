.. WebOOT documentation master file, created by
   sphinx-quickstart on Thu Apr  4 14:34:05 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to WebOOT's documentation!
==================================

Links
-----

* Mailing list: `send email <mailto:weboot-users@cern.ch>`_, or `subscribe <https://e-groups.cern.ch/e-groups/EgroupsSubscription.do?egroupName=weboot-users>`_.
* Documentation: https://weboot.readthedocs.org/
* Code / issues / contribute: https://github.com/rootpy/WebOOT
* Installation instructions: https://github.com/rootpy/WebOOT/README.md

Documentation
-------------

.. toctree::
   :maxdepth: 2

   tutorial

At the moment WebOOT API docs are not online. To generate them locally run::

	cd docs
	sphinx-apidoc ../weboot/ -o api
	make html
	# At the moment this hangs on exit
	# Simply kill the process after it prints "build succeeded"
	open _build/html/py-modindex.html

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

