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

Edit handlers
-------------

Settings use edit handlers much like the rest of Wagtail.  Add a ``panels`` setting to your model defining all the edit handlers required:

.. code-block:: python

    @register_setting
    class ImportantPages(BaseSetting):
        donate_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL)
        sign_up_page = models.ForeignKey(
            'wagtailcore.Page', null=True, on_delete=models.SET_NULL)

        panels = [
            PageChooserPanel('donate_page'),
            PageChooserPanel('sign_up_page'),
        ]

Appearance
----------

You can change the label used in the menu by changing the `verbose_name <https://docs.djangoproject.com/en/dev/ref/models/options/#verbose-name>`_ of your model.

You can add an icon to the menu by passing an 'icon' argument to the ``register_setting`` decorator:

.. code-block:: python

    @register_setting(icon='icon-placeholder')
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

If access to a setting is required in the code, the :func:`~wagtail.contrib.settings.models.BaseSetting.for_site` method will retrieve the setting for the supplied site:

.. code-block:: python

    def view(request):
        social_media_settings = SocialMediaSettings.for_site(request.site)
        ...

Using in templates
------------------

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

If you are not in a ``RequestContext``, then context processors will not have run, and the ``settings`` variable will not be availble. To get the ``settings``, use the provided ``{% get_settings %}`` template tag. If a ``request`` is in the template context, but for some reason it is not a ``RequestContext``, just use ``{% get_settings %}``:

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
