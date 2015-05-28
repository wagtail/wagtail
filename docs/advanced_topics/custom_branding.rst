Custom branding
===============

In your projects with Wagtail, you may wish to replace elements such as the Wagtail logo within the admin interface with your own branding. This can be done through Django's template inheritance mechanism, along with the `django-overextends <https://github.com/stephenmcd/django-overextends>`_ package.

Install ``django-overextends`` with ``pip install django-overextends`` (or add ``django-overextends`` to your project's requirements file), and add ``'overextends'`` to your project's ``INSTALLED_APPS``. You now need to create a ``templates/wagtailadmin/`` folder within one of your apps - this may be an existing one, or a new one created for this purpose, for example, ``dashboard``. This app must be registered in ``INSTALLED_APPS`` before ``wagtail.wagtailadmin``::

    INSTALLED_APPS = (
      # ...

      'overextends',
      'dashboard',
      
      'wagtail.wagtailcore',
      'wagtail.wagtailadmin',
      
      # ...
    )

The template blocks that are available to be overridden are as follows:

``branding_logo``
-----------------

To replace the default logo, create a template file ``dashboard/templates/wagtailadmin/base.html`` that overrides the block ``branding_logo``::

    {% overextends "wagtailadmin/base.html" %}
    
    {% block branding_logo %}
        <img src="{{ STATIC_URL }}images/custom-logo.svg" alt="Custom Project" width="80" />
    {% endblock %}

``branding_login``
------------------

To replace the login message, create a template file ``dashboard/templates/wagtailadmin/login.html`` that overrides the block ``branding_login``::

    {% overextends "wagtailadmin/login.html" %}

    {% block branding_login %}Sign in to Frank's Site{% endblock %}

``branding_welcome``
--------------------

To replace the welcome message on the dashboard, create a template file ``dashboard/templates/wagtailadmin/home.html`` that overrides the block ``branding_welcome``::

    {% overextends "wagtailadmin/home.html" %}

    {% block branding_welcome %}Welcome to Frank's Site{% endblock %}
