====================
Internationalisation
====================

This document describes the internationalisation features of Wagtail and how to create multi-lingual sites.

Wagtail uses Django's `Internationalisation framework <https://docs.djangoproject.com/en/1.8/topics/i18n/>`_ so most of the steps are the same as other Django projects.


.. contents::


Wagtail admin translations
==========================

The Wagtail admin backend has been translated into many different languages. You can find a list of currently available translations on Wagtail's `Transifex page <https://www.transifex.com/torchbox/wagtail/>`_. (Note: if you're using an old version of Wagtail, this page may not accurately reflect what languages you have available).

If your language isn't listed on that page, you can easily contribute new languages or correct mistakes. Sign up and submit changes to `Transifex <https://www.transifex.com/torchbox/wagtail/>`_. Translation updates are typically merged into an official release within one month of being submitted.

Change Wagtail admin language on a per user basis
=================================================
.. versionadded:: 1.10


Logged-in users can set their preferred language from ``/admin/account/``.
By default, Wagtail provides a list of languages that have a >= 90% translation coverage.
It is possible to override this list via the :ref:`WAGTAILADMIN_PERMITTED_LANGUAGES <WAGTAILADMIN_PERMITTED_LANGUAGES>` setting.

In case there is zero or one language permitted, the form will be hidden.

If there is no language selected by the user, the ``LANGUAGE_CODE`` wil be used.


Changing the primary language of your Wagtail installation
==========================================================

The default language of Wagtail is ``en-us`` (American English). You can change this by tweaking a couple of Django settings:

 - Make sure `USE_I18N <https://docs.djangoproject.com/en/1.8/ref/settings/#use-i18n>`_ is set to ``True``
 - Set `LANGUAGE_CODE <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-LANGUAGE_CODE>`_ to your websites' primary language

If there is a translation available for your language, the Wagtail admin backend should now be in the language you've chosen.


Creating sites with multiple languages
======================================

You can create sites with multiple language support by leveraging Django's `translation features <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/>`_.

This section of the documentation will show you how to use Django's translation features with Wagtail and also describe a couple of methods for storing/retrieving translated content using Wagtail pages.


Enabling multiple language support
----------------------------------

Firstly, make sure the `USE_I18N <https://docs.djangoproject.com/en/1.8/ref/settings/#use-i18n>`_ Django setting is set to ``True``.

To enable multi-language support, add ``django.middleware.locale.LocaleMiddleware`` to your ``MIDDLEWARE_CLASSES``:

.. code-block:: python

    MIDDLEWARE_CLASSES = (
        ...

        'django.middleware.locale.LocaleMiddleware',
    )

This middleware class looks at the user's browser language and sets the `language of the site accordingly <https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#how-django-discovers-language-preference>`_.


Serving different languages from different URLs
-----------------------------------------------

Just enabling the multi-language support in Django sometimes may not be enough. By default, Django will serve different languages of the same page with the same URL. This has a couple of drawbacks:

 - Users cannot change language without changing their browser settings
 - It may not work well with various caching setups (as content varies based on browser settings)

Django's ``i18n_patterns`` feature, when enabled, prefixes the URLs with the language code (eg ``/en/about-us``). Users are forwarded to their preferred version, based on browser language, when they first visit the site.

This feature is enabled through the project's root URL configuration. Just put the views you would like to have this enabled for in an ``i18n_patterns`` list and append that to the other URL patterns:

.. code-block:: python

    # mysite/urls.py

    from django.conf.urls import include, url
    from django.conf.urls.i18n import i18n_patterns
    from django.conf import settings
    from django.contrib import admin

    from wagtail.wagtailadmin import urls as wagtailadmin_urls
    from wagtail.wagtaildocs import urls as wagtaildocs_urls
    from wagtail.wagtailcore import urls as wagtail_urls


    urlpatterns = [
        url(r'^django-admin/', include(admin.site.urls)),

        url(r'^admin/', include(wagtailadmin_urls)),
        url(r'^documents/', include(wagtaildocs_urls)),
    ]


    urlpatterns += i18n_patterns(
        # These URLs will have /<language_code>/ appended to the beginning

        url(r'^search/$', 'search.views.search', name='search'),

        url(r'', include(wagtail_urls)),
    )

You can implement switching between languages by changing the part at the beginning of the URL. As each language has its own URL, it also works well with just about any caching setup.


Translating templates
---------------------

Static text in templates needs to be marked up in a way that allows Django's ``makemessages`` command to find and export the strings for translators and also allow them to switch to translated versions on the when the template is being served.

As Wagtail uses Django's templates, inserting this markup and the workflow for exporting and translating the strings is the same as any other Django project.

See: https://docs.djangoproject.com/en/1.8/topics/i18n/translation/#internationalization-in-template-code


Translating content
-------------------

The most common approach for translating content in Wagtail is to duplicate each translatable text field, providing a separate field for each language.

This section will describe how to implement this method manually but there is a third party module you can use, `wagtail modeltranslation <https://github.com/infoportugal/wagtail-modeltranslation>`_, which may be quicker if it meets your needs.


**Duplicating the fields in your model**

For each field you would like to be translatable, duplicate it for every language you support and suffix it with the language code:

.. code-block:: python

    class BlogPage(Page):

        title_fr = models.CharField(max_length=255)

        body_en = StreamField(...)
        body_fr = StreamField(...)

        # Language-independent fields don't need to be duplicated
        thumbnail_image = models.ForeignKey('wagtailimages.image', ...)

.. note::

    We only define the French version of the ``title`` field as Wagtail already provides the English version for us.


**Organising the fields in the admin interface**

You can either put all the fields with their translations next to each other on the "content" tab or put the translations for other languages on different tabs.

See :ref:`customising_the_tabbed_interface` for information on how to add more tabs to the admin interface.


**Accessing the fields from the template**

In order for the translations to be shown on the site frontend, the correct field needs to be used in the template based on what language the client has selected.

Having to add language checks every time you display a field in a template, could make your templates very messy. Here's a little trick that will allow you to implement this while keeping your templates and model code clean.

You can use a snippet like the following to add accessor fields on to your page model. These accessor fields will point at the field that contains the language the user has selected.

Copy this into your project and make sure it's imported in any ``models.py`` files that contain a ``Page`` with translated fields. It will require some modification to support different languages.

.. code-block:: python

    from django.utils import translation

    class TranslatedField(object):
        def __init__(self, en_field, fr_field):
            self.en_field = en_field
            self.fr_field = fr_field

        def __get__(self, instance, owner):
            if translation.get_language() == 'fr':
                return getattr(instance, self.fr_field)
            else:
                return getattr(instance, self.en_field)

Then, for each translated field, create an instance of ``TranslatedField`` with a nice name (as this is the name your templates will reference).

For example, here's how we would apply this to the above ``BlogPage`` model:

.. code-block:: python

    class BlogPage(Page):
        ...

        translated_title = TranslatedField(
            'title',
            'title_fr',
        )
        body = TranslatedField(
            'body_en',
            'body_fr',
        )


Finally, in the template, reference the accessors instead of the underlying database fields:

.. code-block:: html+django

    {{ page.translated_title }}

    {{ page.body }}


Other approaches
----------------

.. toctree::

    duplicate_tree
