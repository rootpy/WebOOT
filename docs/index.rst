.. WebOOT documentation master file, created by
   sphinx-quickstart on Thu Apr  4 14:34:05 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to WebOOT's documentation!
==================================

WebOOT is a `ROOT <http://root.cern.ch/>`_ viewer for the web.

Links
-----

* Website: https://github.com/rootpy/WebOOT
* Documentation: https://weboot.readthedocs.org/
* Mailing list: `send email <mailto:weboot-users@cern.ch>`_, or `subscribe <https://e-groups.cern.ch/e-groups/EgroupsSubscription.do?egroupName=weboot-users>`_.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   tutorial

At the moment WebOOT API docs are not online. To generate them locally run::

	cd docs
	sphinx-apidoc ../weboot/ -o api
	make html
	open _build/html/py-modindex.html

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

