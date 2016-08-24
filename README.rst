****************************
HearThisAt
****************************

.. image:: https://img.shields.io/pypi/v/HearThisAt.svg?style=flat
    :target: https://pypi.python.org/pypi/HearThisAt/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/HearThisAt.svg?style=flat
    :target: https://pypi.python.org/pypi/HearThisAt/
    :alt: Number of PyPI downloads

.. image:: https://img.shields.io/travis/simare/hearthisat/master.svg?style=flat
    :target: https://travis-ci.org/simare/hearthisat
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/simare/hearthisat/master.svg?style=flat
   :target: https://coveralls.io/r/simare/hearthisat
   :alt: Test coverage

playing music from hearthis.at


Installation
============

Install by running::

    pip install HearThisAt

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


Configuration
=============

Before starting Mopidy, you must add configuration for
HearThisAt to your Mopidy configuration file::

    [hearthisat]
    enabled = true
    email = <email>
    password = <password>


Project resources
=================

- `Source code <https://github.com/simare/hearthisat>`_
- `Issue tracker <https://github.com/simare/hearthisat/issues>`_


Changelog
=========
v0.1.1
----------------------------------------
- listing users playlists and such
- removed commented code
- known issues: pagination of search results missing
v0.1.0
----------------------------------------

- Initial release.
