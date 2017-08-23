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

.. _edit_handlers_settings:

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

You can also customize the editor handlers :ref:`like you would do for Page model <customising_the_tabbed_interface>`
with a custom ``edit_handler`` attribute:

.. code-block:: python

    from wagtail.wagtailadmin.edit_handlers import TabbedInterface, ObjectList

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

You can change the label used in the menu by changing the `verbose_name <https://docs.djangoproject.com/en/dev/ref/models/options/#verbose-name>`_ of your model.

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

If access to a setting is required in the code, the :func:`~wagtail.contrib.settings.models.BaseSetting.for_site` method will retrieve the setting for the supplied site:

.. code-block:: python

    def view(request):
        social_media_settings = SocialMediaSettings.for_site(request.site)
        ...

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
        or Instagram at @{{ social_settings.Instagram }}.
    {% endwith %}

Or, alternately, using the ``set`` tag:

.. code-block:: html+jinja

    {% set social_settings=settings("app_label.SocialMediaSettings") %}
