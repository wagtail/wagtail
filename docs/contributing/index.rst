Contributing to Wagtail
=======================

Issues
~~~~~~

The easiest way to contribute to Wagtail is to tell us how to improve it! First, check to see if your bug or feature request has already been submitted at `github.com/wagtail/wagtail/issues <https://github.com/wagtail/wagtail/issues>`_. If it has, and you have some supporting information which may help us deal with it, comment on the existing issue. If not, please `create a new one <https://github.com/wagtail/wagtail/issues/new>`_, providing as much relevant context as possible. For example, if you're experiencing problems with installation, detail your environment and the steps you've already taken. If something isn't displaying correctly, tell us what browser you're using, and include a screenshot if possible.

If your bug report is a security issue, **do not** report it with an issue. Please read our ​guide to :doc:`reporting security issues <security>`.

.. toctree::
    :maxdepth: 2

    issue_tracking

Pull requests
~~~~~~~~~~~~~

If you're a Python or Django developer, `fork it <https://github.com/wagtail/wagtail/>`_ and read the :ref:`developing docs <developing>` to get stuck in! We welcome all contributions, whether they solve problems which are specific to you or they address existing issues. If you're stuck for ideas, pick something from the `issue list <https://github.com/wagtail/wagtail/issues?state=open>`_, or email us directly on `hello@wagtail.io <mailto:hello@wagtail.io>`_ if you'd like us to suggest something!

For large-scale changes, we'd generally recommend breaking them down into smaller pull requests that achieve a single well-defined task and can be reviewed individually. If this isn't possible, we recommend opening a pull request on the `Wagtail RFCs <https://github.com/wagtail/rfcs/>`_ repository, so that there's a chance for the community to discuss the change before it gets implemented.

.. toctree::
    :maxdepth: 2

    developing
    committing


Translations
~~~~~~~~~~~~

Wagtail has internationalisation support so if you are fluent in a non-English language you can contribute by localising the interface.

Translation work should be submitted through `Transifex <https://www.transifex.com/projects/p/wagtail/>`_.


Other contributions
~~~~~~~~~~~~~~~~~~~

We welcome contributions to all aspects of Wagtail. If you would like to improve the design of the user interface, or extend the documentation, please submit a pull request as above. If you're not familiar with Github or pull requests, `contact us directly <mailto:hello@wagtail.io>`_ and we'll work something out.



Developing packages for Wagtail
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you are developing packages for Wagtail, you can add the following `PyPI <https://pypi.org/>`_ classifiers:

* `Framework :: Wagtail <https://pypi.org/search/?c=Framework+%3A%3A+Wagtail>`_
* `Framework :: Wagtail :: 1 <https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+1>`_
* `Framework :: Wagtail :: 2 <https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+2>`_

You can also find a curated list of awesome packages, articles, and other cool resources from the Wagtail community at `Awesome Wagtail <https://github.com/springload/awesome-wagtail>`_.


More information
~~~~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 2

    styleguide
    general_guidelines
    python_guidelines
    html_guidelines
    css_guidelines
    javascript_guidelines
    documentation_guidelines
    documentation-modes
    security
    release_process
