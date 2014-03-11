Sphinx docs, automatically built at docs.wagtail.io when the master branch is committed to Github. To build locally, install Sphinx and the RTD theme:

    pip install Sphinx
    pip install sphinx-rtd-theme

Then ``make html`` from this directory, and open ``_build/html/index.html`` in your browser.

To auto-build your local docs when you save:

    pip install watchdog
    $ watchmedo shell-command \
              --patterns="*.rst" \
              --ignore-pattern='_build/*' \
              --recursive \
              --command='make html'
