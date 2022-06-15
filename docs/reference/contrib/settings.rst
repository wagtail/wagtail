.. _settings:

=============
Site settings
=============

You can define settings for your site that are editable by administrators in the Wagtail admin. These settings can be accessed in code, as well as in templates.

To use these settings, you must add ``wagtail.contrib.settings`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS += [
        'wagtail.contrib.settings',
    ]


Defining settings
=================

Create a model that inherits from ``BaseSetting``, and register it using the ``register_setting`` decorator:

.. code-block:: python

    from django.db import models
    from wagtail.contrib.settings.models import BaseSetting, register_setting

    @register_setting
    class SocialMediaSettings(BaseSetting):
        facebook = models.URLField(
            help_text='Your Facebook page URL')
        instagram = models.CharField(
            max_length=255, help_text='Your Instagram username, without the @')
        trip_advisor = models.URLField(
            help_text='Your Trip Advisor page URL')
        youtube = models.URLField(
            help_text='Your YouTube channel or user account URL')


A 'Social media settings' link will appear in the Wagtail admin 'Settings' menu.

.. _edit_handlers_settings:

Edit handlers
-------------

Settings use edit handlers much like the rest of Wagtail.  Add a ``panels`` setting to your model defining all the edit handlers required:

.. code-block:: python

    @register_setting
    class ImportantPages(BaseSetting):
        donate_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+')
        sign_up_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+')

        panels = [
            FieldPanel('donate_page'),
            FieldPanel('sign_up_page'),
        ]

You can also customise the editor handlers :ref:`like you would do for Page model <customising_the_tabbed_interface>`
with a custom ``edit_handler`` attribute:

.. code-block:: python

    from wagtail.admin.panels import TabbedInterface, ObjectList

    @register_setting
    class MySettings(BaseSetting):
        # ...
        first_tab_panels = [
            FieldPanel('field_1'),
        ]
        second_tab_panels = [
            FieldPanel('field_2'),
        ]

        edit_handler = TabbedInterface([
            ObjectList(first_tab_panels, heading='First tab'),
            ObjectList(second_tab_panels, heading='Second tab'),
        ])


Appearance
----------

You can change the label used in the menu by changing the :attr:`~django.db.models.Options.verbose_name` of your model.

You can add an icon to the menu by passing an 'icon' argument to the ``register_setting`` decorator:

.. code-block:: python

    @register_setting(icon='placeholder')
    class SocialMediaSettings(BaseSetting):
        class Meta:
            verbose_name = 'social media accounts'
        ...

For a list of all available icons, please see the :ref:`styleguide`.

Using the settings
==================

Settings are designed to be used both in Python code, and in templates.

Using in Python
---------------

If you require access to a setting in a view, the :func:`~wagtail.contrib.settings.models.BaseSetting.for_request` method allows you to retrieve the relevant settings for the current request:

.. code-block:: python

    def view(request):
        social_media_settings = SocialMediaSettings.for_request(request)
        ...

In places where the request is unavailable, but you know the ``Site`` you wish to retrieve settings for, you can use :func:`~wagtail.contrib.settings.models.BaseSetting.for_site` instead:

.. code-block:: python

    social_media_settings =  SocialMediaSettings.for_site(user.origin_site)

Using in Django templates
-------------------------

Add the ``settings`` context processor to your settings:

.. code-block:: python

    TEMPLATES = [
        {
            ...

            'OPTIONS': {
                'context_processors': [
                    ...

                    'wagtail.contrib.settings.context_processors.settings',
                ]
            }
        }
    ]


Then access the settings through ``{{ settings }}``:

.. code-block:: html+django

    {{ settings.app_label.SocialMediaSettings.instagram }}

.. note:: Replace ``app_label`` with the label of the app containing your settings model.

If you are not in a ``RequestContext``, then context processors will not have run, and the ``settings`` variable will not be available. To get the ``settings``, use the provided ``{% get_settings %}`` template tag. If a ``request`` is in the template context, but for some reason it is not a ``RequestContext``, just use ``{% get_settings %}``:

.. code-block:: html+django

    {% load wagtailsettings_tags %}
    {% get_settings %}
    {{ settings.app_label.SocialMediaSettings.instagram }}

If there is no ``request`` available in the template at all, you can use the settings for the default Wagtail site instead:

.. code-block:: html+django

    {% load wagtailsettings_tags %}
    {% get_settings use_default_site=True %}
    {{ settings.app_label.SocialMediaSettings.instagram }}

.. note:: You can not reliably get the correct settings instance for the current site from this template tag if the request object is not available. This is only relevant for multisite instances of Wagtail.

By default, the tag will create or update a ``settings`` variable in the context. If you want to
assign to a different context variable instead, use ``{% get_settings as other_variable_name %}``:

.. code-block:: html+django

    {% load wagtailsettings_tags %}
    {% get_settings as wagtail_settings %}
    {{ wagtail_settings.app_label.SocialMediaSettings.instagram }}

.. _settings_tag_jinja2:

Using in Jinja2 templates
-------------------------

Add ``wagtail.contrib.settings.jinja2tags.settings`` extension to your Jinja2 settings:

.. code-block:: python

    TEMPLATES = [
        # ...
        {
            'BACKEND': 'django.template.backends.jinja2.Jinja2',
            'APP_DIRS': True,
            'OPTIONS': {
                'extensions': [
                    # ...
                    'wagtail.contrib.settings.jinja2tags.settings',
                ],
            },
        }
    ]


Then access the settings through the ``settings()`` template function:

.. code-block:: html+jinja

    {{ settings("app_label.SocialMediaSettings").twitter }}

.. note:: Replace ``app_label`` with the label of the app containing your settings model.

This will look for a ``request`` variable in the template context, and find the correct site to use from that. If for some reason you do not have a ``request`` available, you can instead use the settings defined for the default site:

.. code-block:: html+jinja

    {{ settings("app_label.SocialMediaSettings", use_default_site=True).instagram }}

You can store the settings instance in a variable to save some typing, if you have to use multiple values from one model:

.. code-block:: html+jinja

    {% with social_settings=settings("app_label.SocialMediaSettings") %}
        Follow us on Twitter at @{{ social_settings.twitter }},
        or Instagram at @{{ social_settings.instagram }}.
    {% endwith %}

Or, alternately, using the ``set`` tag:

.. code-block:: html+jinja

    {% set social_settings=settings("app_label.SocialMediaSettings") %}


Utilising ``select_related`` to improve efficiency
--------------------------------------------------

For models with foreign key relationships to other objects (e.g. pages),
which are very often needed to output values in templates, you can set
the ``select_related`` attribute on your model to have Wagtail utilise
Django's `QuerySet.select_related() <https://docs.djangoproject.com/en/stable/ref/models/querysets/#select-related>`_
method to fetch the settings object and related objects in a single query.
With this, the initial query is more complex, but you will be able to
freely access the foreign key values without any additional queries,
making things more efficient overall.

Building on the ``ImportantPages`` example from the previous section, the
following shows how ``select_related`` can be set to improve efficiency:

.. code-block:: python
    :emphasize-lines: 4,5

    @register_setting
    class ImportantPages(BaseSetting):

        # Fetch these pages when looking up ImportantPages for or a site
        select_related = ["donate_page", "sign_up_page"]

        donate_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+')
        sign_up_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL, related_name='+')

        panels = [
            FieldPanel('donate_page'),
            FieldPanel('sign_up_page'),
        ]

With these additions, the following template code will now trigger
a single database query instead of three (one to fetch the settings,
and two more to fetch each page):

.. code-block:: html+django

    {% load wagtailcore_tags %}
    {% pageurl settings.app_label.ImportantPages.donate_page %}
    {% pageurl settings.app_label.ImportantPages.sign_up_page %}


Utilising the ``page_url`` setting shortcut
-------------------------------------------

If, like in the previous section, your settings model references pages,
and you often need to output the URLs of those pages in your project,
you can likely use the setting model's ``page_url`` shortcut to do that more
cleanly. For example, instead of doing the following:

.. code-block:: html+django

    {% load wagtailcore_tags %}
    {% pageurl settings.app_label.ImportantPages.donate_page %}
    {% pageurl settings.app_label.ImportantPages.sign_up_page %}

You could write:

.. code-block:: html+django

    {{ settings.app_label.ImportantPages.page_url.donate_page }}
    {{ settings.app_label.ImportantPages.page_url.sign_up_page }}

Using the ``page_url`` shortcut has a few of advantages over using the tag:

1.  The 'specific' page is automatically fetched to generate the URL,
    so you don't have to worry about doing this (or forgetting to do this)
    yourself.
2.  The results are cached, so if you need to access the same page URL
    in more than one place (e.g. in a form and in footer navigation), using
    the ``page_url`` shortcut will be more efficient.
3.  It's more concise, and the syntax is the same whether using it in templates
    or views (or other Python code), allowing you to write more consistent
    code.

When using the ``page_url`` shortcut, there are a couple of points worth noting:

1.  The same limitations that apply to the `{% pageurl %}` tag apply to the
    shortcut: If the settings are accessed from a template context where the
    current request is not available, all URLs returned will include the
    site's scheme/domain, and URL generation will not be quite as efficient.
2.  If using the shortcut in views or other Python code, the method will
    raise an ``AttributeError`` if the attribute you request from ``page_url``
    is not an attribute on the settings object.
3.  If the settings object DOES have the attribute, but the attribute returns
    a value of ``None`` (or something that is not a ``Page``), the shortcut
    will return an empty string.
