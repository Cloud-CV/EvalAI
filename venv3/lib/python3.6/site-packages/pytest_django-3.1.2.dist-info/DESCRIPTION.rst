.. image:: https://secure.travis-ci.org/pytest-dev/pytest-django.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/pytest-dev/pytest-django

Welcome to pytest-django!
=========================

pytest-django allows you to test your Django project/applications with the
`pytest testing tool <http://pytest.org/>`_.

* `Quick start / tutorial
  <https://pytest-django.readthedocs.io/en/latest/tutorial.html>`_
* `Changelog <https://pytest-django.readthedocs.io/en/latest/changelog.html>`_
* Full documentation: https://pytest-django.readthedocs.io/en/latest/
* `Contribution docs
  <https://pytest-django.readthedocs.io/en/latest/contributing.html>`_
* Version compatibility:

  * Django: 1.7-1.10 and latest master branch (compatible at the time of each release)
  * Python: CPython 2.7,3.3-3.5 or PyPy 2,3
  * pytest: >2.9.x

* Licence: BSD
* Project maintainers: Andreas Pelme, Floris Bruynooghe and Daniel Hahler
* `All contributors <https://github.com/pytest-dev/pytest-django/contributors>`_
* Github repository: https://github.com/pytest-dev/pytest-django
* `Issue tracker <http://github.com/pytest-dev/pytest-django/issues>`_
* `Python Package Index (PyPI) <https://pypi.python.org/pypi/pytest-django/>`_

Install pytest-django
---------------------

::

    pip install pytest-django

Why would I use this instead of Django's `manage.py test` command?
------------------------------------------------------------------

Running your test suite with pytest-django allows you to tap into the features
that are already present in pytest. Here are some advantages:

* `Manage test dependencies with pytest fixtures. <http://pytest.org/latest/fixture.html>`_
* Less boilerplate tests: no need to import unittest, create a subclass with methods. Write tests as regular functions.
* Database re-use: no need to re-create the test database for every test run.
* Run tests in multiple processes for increased speed (with the pytest-xdist plugin).
* Make use of other `pytest plugins <http://pytest.org/latest/plugins.html>`_.
* Works with both worlds: Existing unittest-style TestCase's still work without any modifications.

See the `pytest documentation <http://pytest.org/latest/>`_ for more information on pytest itself.


