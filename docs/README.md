# Wagtail docs

These are Sphinx docs, automatically built at http://docs.wagtail.io when the master branch is committed to Github. To build them locally, install Wagtail's development requirements (in the root Wagtail directory):

    pip install requirements-dev.txt

To build the documentation for browsing, from this directory run: 

    ``make html`` 

then open ``_build/html/index.html`` in a browser.

To rebuild automatically while editing the documentation, from this directory run:

    ``sphinx-autobuild . _build``

The online editor at http://rst.ninjs.org/ is a helpful tool for checking reStructuredText syntax.
