cnx-repo README
==================

Getting Started
---------------

- cd <directory containing this file>

- $venv/bin/python setup.py develop

- $venv/bin/initialize_cnx-repo_db development.ini

- $venv/bin/pserve development.ini

gevent is currently not supported on Python 3. However, there is a
fork which has made experimental changes that does support Python 3.

::

    git clone https://github.com/fantix/gevent.git $venv/gevent

Installing gevent in a virtual environment will require cython (for
greenlet to build) and the exportation/activation of the virtual
environment.

::

    $venv/bin/pip install cython
    export PATH=$venv/bin:$PATH
    $venv/bin/pip install $venv/gevent
