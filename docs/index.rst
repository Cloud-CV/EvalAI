.. EvalAI documentation master file, created by
   sphinx-quickstart on Fri Oct 21 07:36:55 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to EvalAI's documentation!
==================================

|Build Status| |Coverage Status| |Requirements Status| |Code Health|

EvalAI is an open source web application that helps researchers,
students and data-scientists to create, collaborate and participate in
various AI challenges organized round the globe.

How to setup
------------

| Setting up EvalAI on your local machine is really easy. Follow this guide to setup your development machine.

#. Install `git`_, `postgresql`_ and `virtualenv`_, in your computer, if
   you don’t have it already.

#. Get the source code on your machine via git.

   .. code:: shell

       git clone https://github.com/Cloud-CV/EvalAI.git evalai

#. Create a python virtual environment and install python dependencies.

   .. code:: shell

       cd evalai
       virtualenv venv
       source venv/bin/activate  # run this command everytime before working on project
       pip install -r requirements/dev.txt

#. Change credential in setting/dev.py

   ::

       nano settings/dev.py

   For new postgresql user

   USER: “postgres”;PASSWORD: “”

#. Create an empty postgres database and run database migration.

   ::

       createdb evalai
       python manage.py migrate
       python manage.py sample_data

#. That’s it. Now you can run development server at
   http://127.0.0.1:8000

   ::

       python manage.py runserver --settings=settings.dev


.. _git: https://git-scm.com/downloads
.. _postgresql: http://www.postgresql.org/download/
.. _virtualenv: https://virtualenv.pypa.io/

.. |Build Status| image:: https://travis-ci.org/Cloud-CV/EvalAI.svg?branch=master
   :target: https://travis-ci.org/Cloud-CV/EvalAI
.. |Coverage Status| image:: https://coveralls.io/repos/github/Cloud-CV/EvalAI/badge.svg
   :target: https://coveralls.io/github/Cloud-CV/EvalAI
.. |Requirements Status| image:: https://requires.io/github/Cloud-CV/EvalAI/requirements.svg?branch=master
   :target: https://requires.io/github/Cloud-CV/EvalAI/requirements/?branch=master
.. |Code Health| image:: https://landscape.io/github/Cloud-CV/EvalAI/master/landscape.svg?style=flat
   :target: https://landscape.io/github/Cloud-CV/EvalAI/master

.. toctree::
   :maxdepth: 2

.. include:: contribution.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

