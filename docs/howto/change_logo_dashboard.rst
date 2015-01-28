Change Logo in Dashboard
========================

In your projects with Wagtail, maybe need switch the default logo to other image. For this, you need override the block ``logo_admin``::

    {% extends "wagtailadmin/base.html" %}
    
    {% block admin_logo %}
        <img src="{{ STATIC_URL }}images/custom-logo.svg" alt="Custom Project" width="80" />
    {% endblock %}
    

Save this in your app, for example, ``dashboard`` to ``dashboard/templates/wagtailadmin/base.html`` and register before ``wagtailadmin``::

    INSTALLED_APPS = (
      # ...
      
      'dashboard',
      
      'wagtail.wagtailcore',
      'wagtail.wagtailadmin',
      
      # ...
    )
