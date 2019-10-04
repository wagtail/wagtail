.. _developing:

Development
===========

Setting up a local copy of `the Wagtail git repository <https://github.com/wagtail/wagtail>`_ is slightly more involved than running a release package of Wagtail, as it requires `Node.js <https://nodejs.org/>`_ and NPM for building Javascript and CSS assets. (This is not required when running a release version, as the compiled assets are included in the release package.)

If you're happy to develop on a virtual machine, the `vagrant-wagtail-develop <https://github.com/wagtail/vagrant-wagtail-develop>`_ setup script is the fastest way to get up and running. This will provide you with a running instance of the `Wagtail Bakery demo site <https://github.com/wagtail/bakerydemo/>`_, with the Wagtail and bakerydemo codebases available as shared folders for editing on your host machine.

(Build scripts for other platforms would be very much welcomed - if you create one, please let us know via the `Wagtail Developers group <https://groups.google.com/forum/#!forum/wagtail-developers>`_!)

If you'd prefer to set up all the components manually, read on. These instructions assume that you're familiar with using pip and virtualenv to manage Python packages.


Setting up the Wagtail codebase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Node.js, version 8. Instructions for installing Node.js can be found on the `Node.js download page <https://nodejs.org/download/>`_.
You can also use Node version manager (nvm) since Wagtail supplies a ``.nvmrc`` file in the root of the project with the minimum required Node version - see nvm's `installation instructions <https://github.com/creationix/nvm>`_.

You will also need to install the **libjpeg** and **zlib** libraries, if you haven't done so already - see Pillow's `platform-specific installation instructions <http://pillow.readthedocs.org/en/latest/installation.html#external-libraries>`_.

Clone a copy of `the Wagtail codebase <https://github.com/wagtail/wagtail>`_:

.. code-block:: console

    $ git clone https://github.com/wagtail/wagtail.git
    $ cd wagtail

With your preferred virtualenv activated, install the Wagtail package in development mode with the included testing and documentation dependencies:

.. code-block:: console

    $ pip install -e '.[testing,docs]' -U

Install Node through nvm (optional):

.. code-block:: console

    $ nvm install

Install the tool chain for building static assets:

.. code-block:: console

    $ npm install --no-save

Compile the assets:

.. code-block:: console

    $ npm run build

Any Wagtail sites you start up in this virtualenv will now run against this development instance of Wagtail.  We recommend using the `Wagtail Bakery demo site <https://github.com/wagtail/bakerydemo/>`_ as a basis for developing Wagtail. Keep in mind that the setup steps for a Wagtail site may include installing a release version of Wagtail, which will override the development version you've just set up. In this case, you should install the site before running the ``pip install -e`` step, or re-run that step after the site is installed.

.. _testing:

Testing
~~~~~~~

From the root of the Wagtail codebase, run the following command to run all the tests:

.. code-block:: console

    $ python runtests.py

Running only some of the tests
------------------------------

At the time of writing, Wagtail has well over 2500 tests, which takes a while to
run. You can run tests for only one part of Wagtail by passing in the path as
an argument to ``runtests.py`` or ``tox``:

.. code-block:: console

    $ # Running in the current environment
    $ python runtests.py wagtail.core

    $ # Running in a specified Tox environment
    $ tox -e py36-dj20-sqlite-noelasticsearch wagtail.core

    $ # See a list of available Tox environments
    $ tox -l

You can also run tests for individual TestCases by passing in the path as
an argument to ``runtests.py``

.. code-block:: console

    $ # Running in the current environment
    $ python runtests.py wagtail.core.tests.test_blocks.TestIntegerBlock

    $ # Running in a specified Tox environment
    $ tox -e py36-dj20-sqlite-noelasticsearch wagtail.core.tests.test_blocks.TestIntegerBlock

Running migrations for the test app models
------------------------------------------

You can create migrations for the test app by running the following from the Wagtail root.

.. code-block:: console

    $ django-admin.py makemigrations --settings=wagtail.tests.settings


Testing against PostgreSQL
--------------------------

By default, Wagtail tests against SQLite. You can switch to using PostgreSQL by
using the ``--postgres`` argument:

.. code-block:: console

    $ python runtests.py --postgres

If you need to use a different user, password or host. Use the ``PGUSER``, ``PGPASSWORD`` and ``PGHOST`` environment variables.

Testing against a different database
------------------------------------

If you need to test against a different database, set the ``DATABASE_ENGINE``
environment variable to the name of the Django database backend to test against:

.. code-block:: console

    $ DATABASE_ENGINE=django.db.backends.mysql python runtests.py

This will create a new database called ``test_wagtail`` in MySQL and run
the tests against it.

Testing Elasticsearch
---------------------

You can test Wagtail against Elasticsearch by passing the ``--elasticsearch``
argument to ``runtests.py``:

.. code-block:: console

    $ python runtests.py --elasticsearch


Wagtail will attempt to connect to a local instance of Elasticsearch
(``http://localhost:9200``) and use the index ``test_wagtail``.

If your Elasticsearch instance is located somewhere else, you can set the
``ELASTICSEARCH_URL`` environment variable to point to its location:

.. code-block:: console

    $ ELASTICSEARCH_URL=http://my-elasticsearch-instance:9200 python runtests.py --elasticsearch

Browser and device support
--------------------------

Wagtail is meant to be used on a wide variety of devices and browsers. Supported browser / device versions include:

=============  =============  =============
Browser        Device/OS      Version(s)
=============  =============  =============
Mobile Safari  iOS Phone      Last 2
Mobile Safari  iOS Tablet     Last 2
Chrome         Android        Last 2
IE             Desktop        11
Chrome         Desktop        Last 2
MS Edge        Desktop        Last 2
Firefox        Desktop        Latest
Firefox ESR    Desktop        Latest
Safari         macOS          Last 2
=============  =============  =============

We aim for Wagtail to work in those environments. Our development standards ensure that the site is usable on other browsers **and will work on future browsers**. To test on IE, install virtual machines `made available by Microsoft <https://developer.microsoft.com/en-us/microsoft-edge/tools/vms/>`_.

IE 11 is gradually falling out of use, and specific features are unsupported in this browser:

* Rich text copy-paste in the rich text editor.
* Sticky toolbar in the rich text editor.
* Focus outline styles in the main menu & explorer menu.

**Unsupported browsers / devices include:**

=============  =============  =============
Browser        Device/OS      Version(s)
=============  =============  =============
Stock browser  Android        All
IE             Desktop        10 and below
Safari         Windows        All
=============  =============  =============

Accessibility targets
---------------------

We want to make Wagtail accessible for users of a wide variety of assistive technologies. The specific standard we aim for is `WCAG2.1 <https://www.w3.org/TR/WCAG21/>`_, AA level. Wagtail’s administration user interface isn’t accessible at the moment (see `issue #4199 <https://github.com/wagtail/wagtail/issues/4199>`_), but here are specific assistive technologies we aim to test for, and ultimately support:

=============  ====================
Type           Assistive technology
=============  ====================
Screen reader  `NVDA <https://www.nvaccess.org/download/>`_ on Windows with Firefox ESR
Screen reader  `VoiceOver <https://support.apple.com/en-gb/guide/voiceover-guide/welcome/web>`_ on macOS with Safari
Magnification  `Windows Magnifier <https://support.microsoft.com/en-gb/help/11542/windows-use-magnifier>`_
Magnification  macOS Zoom
Voice control  Windows Speech Recognition
Voice control  macOS Dictation
Screen reader  Mobile `VoiceOver <https://support.apple.com/en-gb/guide/voiceover-guide/welcome/web>`_ on iOS, or `TalkBack <https://support.google.com/accessibility/android/answer/6283677?hl=en-GB>`_ on Android
=============  ====================

We aim for Wagtail to work in those environments. Our development standards ensure that the site is usable with other assistive technologies. In practice, testing with assistive technology can be a daunting task that requires specialised training – here are tools we rely on to help identify accessibility issues, to use during development and code reviews:

* `react-axe <https://github.com/dequelabs/react-axe>`_ integrated directly in our build tools, to identify actionable issues. Logs its results in the browser console.
* `Axe <https://chrome.google.com/webstore/detail/axe/lhdoppojpmngadmnindnejefpokejbdd>`_ Chrome extension for more comprehensive automated tests of a given page.
* `Accessibility Insights for Web <https://accessibilityinsights.io/docs/en/web/overview>`_ Chrome extension for semi-automated tests, and manual audits.

Compiling static assets
~~~~~~~~~~~~~~~~~~~~~~~

All static assets such as JavaScript, CSS, images, and fonts for the Wagtail admin are compiled from their respective sources by ``gulp``. The compiled assets are not committed to the repository, and are compiled before packaging each new release. Compiled assets should not be submitted as part of a pull request.

To compile the assets, run:

.. code-block:: console

    $ npm run build

This must be done after every change to the source files. To watch the source files for changes and then automatically recompile the assets, run:

.. code-block:: console

    $ npm start

Compiling the documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Wagtail documentation is built by Sphinx. To install Sphinx and compile the documentation, run:

.. code-block:: console

    $ cd /path/to/wagtail
    $ # Install the documentation dependencies
    $ pip install -e .[docs]
    $ # Compile the docs
    $ cd docs/
    $ make html

The compiled documentation will now be in ``docs/_build/html``.
Open this directory in a web browser to see it.
Python comes with a module that makes it very easy to preview static files in a web browser.
To start this simple server, run the following commands:

.. code-block:: console

    $ cd docs/_build/html/
    $ python -mhttp.server 8080

Now you can open <http://localhost:8080/> in your web browser to see the compiled documentation.

Sphinx caches the built documentation to speed up subsequent compilations.
Unfortunately, this cache also hides any warnings thrown by unmodified documentation source files.
To clear the built HTML and start fresh, so you can see all warnings thrown when building the documentation, run:

.. code-block:: console

    $ cd docs/
    $ make clean
    $ make html

Wagtail also provides a way for documentation to be compiled automatically on each change.
To do this, you can run the following command to see the changes automatically at ``localhost:4000``:

.. code-block:: console

    $ cd docs/
    $ make livehtml


