# Wagtail docs

These are Sphinx docs, automatically built at http://docs.wagtail.io when the master branch is committed to Github. To build them locally, install Sphinx and the RTD theme:

    pip install Sphinx
    pip install sphinx-rtd-theme

Then ``make html`` from this directory, and open ``_build/html/index.html`` in your browser.

We've provided a watchdog script (based on @jacobian's [snippet](http://jacobian.org/writing/auto-building-sphinx/)) to auto-build your local docs when you save them. Install watchdog:

    pip install watchdog

Then run ``./autobuild.sh`` before you start editing.

The online editor at http://rst.ninjs.org/ is a helpful tool for checking reStructuredText syntax.
