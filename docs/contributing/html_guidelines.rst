HTML coding guidelines
======================

We use `Django templates <https://docs.djangoproject.com/en/stable/ref/templates/language/>`_ to author HTML.

Linting HTML
~~~~~~~~~~~~

We use `jinjalint <https://github.com/motet-a/jinjalint>`_ to lint templates. If you have installed Wagtail's testing dependencies (``pip install -e .[testing]``), you can check your code by running ``make lint``.

Principles
~~~~~~~~~~

* Write `valid HTML <https://validator.w3.org/nu/>`_. We target the HTML5 doctype.
* Write `semantic HTML <https://html5doctor.com/element-index/>`_.
* Attach JavaScript behavior with ``data-`` attributes, rather than classes or IDs.
* For comments, use Django templates syntax instead of HTML.
