.. _multi_site_capabilities:

Multi-Site Capabilities
=======================

Overview
--------

Wagtail provides multi-site capability via the :ref:`site-model-ref` model.  One or more sites can be created via the Sites option under the admin Settings menu.  A root page is chosen and a hostname is defined for each site that is created.

:ref:`settings` can be defined by creating a model that inherits from BaseSetting.

While Wagtail provides multi-site capability and adds the site object to the request object, multi-tenant capability is not currently supported.  Therefore, if more than one site is set up, any user who has access to the admin can log in through any hostname.  After logging in, however, user rights that were assigned via Groups are honored with one exception:  When a user has rights to view or edit a particular BaseSetting-derived object, all site-specific instances of that particular object are editable.  However, the BaseSetting-derived object instance that is first presented for editing will be the instance that corresponds to the hostname under which the user is logged in.

Site-Specific Error Pages
-------------------------

Since Wagtail is built on Django, standard Django exceptions are raised (for example, Wagtail raises Http404 when a page is not found).  The error pages returned by these exceptions can be customized in the same way that this customization is normally done in Django - by either placing in one of the folders where templates are stored a template for a particular error message (i.e. ``404.html``) or by providing a `custom view to handle the error`_.   By using the custom view method for overriding the rendering of a particular type of error, a site-specific custom error page can be returned.  To create site-specific custom 404 pages, place the ``handler404`` directive in the same ``urls.py`` file where the Wagtail urls have been included:

.. _custom view to handle the error: https://docs.djangoproject.com/en/dev/topics/http/views/#customizing-error-views

.. code-block:: python

    from yourapp.views import custom404_view

    handler404 = 'yourapp.views.custom404_view'

Then, in the views.py file for your_app, place the conditional logic to return a site-specific error page:

.. code-block:: python

    from django.http import HttpResponseNotFound
    from django.template.loader import render_to_string

    def custom404_view(request, exception):
        if request.site.hostname == 'site1.com':
            return HttpResponseNotFound(render_to_string('404_site1.html', request=request))
        elif request.site.hostname == 'site2.com':
            return HttpResponseNotFound(render_to_string('404_site2.html', request=request))
        else:
            return HttpResponseNotFound(render_to_string('404.html', request=request))
