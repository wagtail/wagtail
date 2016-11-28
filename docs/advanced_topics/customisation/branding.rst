.. _custom_branding:

Custom branding
===============

In your projects with Wagtail, you may wish to replace elements such as the Wagtail logo within the admin interface with your own branding. This can be done through Django's template inheritance mechanism.

.. note::
   Using ``{% extends %}`` in this way on a template you're currently overriding is only supported in Django 1.9 and above. On Django 1.8, you will need to use `django-overextends <https://github.com/stephenmcd/django-overextends>`_ instead.

You need to create a ``templates/wagtailadmin/`` folder within one of your apps - this may be an existing one, or a new one created for this purpose, for example, ``dashboard``. This app must be registered in ``INSTALLED_APPS`` before ``wagtail.wagtailadmin``:

.. code-block:: python

    INSTALLED_APPS = (
        # ...

        'dashboard',

        'wagtail.wagtailcore',
        'wagtail.wagtailadmin',

        # ...
    )

The template blocks that are available to be overridden are as follows:

``branding_logo``
-----------------

To replace the default logo, create a template file ``dashboard/templates/wagtailadmin/base.html`` that overrides the block ``branding_logo``:

.. code-block:: html+django

    {% extends "wagtailadmin/base.html" %}
    {% load staticfiles %}

    {% block branding_logo %}
        <img src="{% static 'images/custom-logo.svg' %}" alt="Custom Project" width="80" />
    {% endblock %}

``branding_favicon``
--------------------

To replace the favicon displayed when viewing admin pages, create a template file ``dashboard/templates/wagtailadmin/admin_base.html`` that overrides the block ``branding_favicon``:

.. code-block:: html+django

    {% extends "wagtailadmin/admin_base.html" %}
    {% load staticfiles %}

    {% block branding_favicon %}
        <link rel="shortcut icon" href="{% static 'images/favicon.ico' %}" />
    {% endblock %}

``branding_login``
------------------

To replace the login message, create a template file ``dashboard/templates/wagtailadmin/login.html`` that overrides the block ``branding_login``:

.. code-block:: html+django

    {% extends "wagtailadmin/login.html" %}

    {% block branding_login %}Sign in to Frank's Site{% endblock %}

``branding_welcome``
--------------------

To replace the welcome message on the dashboard, create a template file ``dashboard/templates/wagtailadmin/home.html`` that overrides the block ``branding_welcome``:

.. code-block:: html+django

    {% extends "wagtailadmin/home.html" %}

    {% block branding_welcome %}Welcome to Frank's Site{% endblock %}
