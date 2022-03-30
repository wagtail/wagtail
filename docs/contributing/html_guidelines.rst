HTML coding guidelines
======================

We use `Django templates <https://docs.djangoproject.com/en/stable/ref/templates/language/>`_ to author HTML.

Linting HTML
~~~~~~~~~~~~

We use `curlylint <https://www.curlylint.org/>`_ to lint templates and `djhtml <https://github.com/rtts/djhtml>`_ to format them.
If you have installed Wagtail's testing dependencies (``pip install -e .[testing]``), you can check your code by running ``make lint``, and format your code by running ``make format``. Alternatively you can also run
``make lint-client`` for checking and ``make format-client`` for formatting frontend (html/css/js) only files.

Principles
~~~~~~~~~~

* Write `valid HTML <https://validator.w3.org/nu/>`_. We target the HTML5 doctype.
* Write `semantic HTML <https://html5doctor.com/element-index/>`_.
* Consult `ARIA Authoring Practices <https://w3c.github.io/aria-practices/>`_, in particular `No ARIA is better than Bad ARIA <https://w3c.github.io/aria-practices/#no_aria_better_bad_aria>`_.
* Attach JavaScript behavior with ``data-`` attributes, rather than classes or IDs.
* For comments, use Django templates syntax instead of HTML.
