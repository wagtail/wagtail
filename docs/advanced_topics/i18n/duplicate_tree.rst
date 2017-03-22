===========================================================
Creating a multilingual site (by duplicating the page tree)
===========================================================

This tutorial will show you a method of creating multilingual sites in Wagtail by duplicating the page tree.

For example::

    /
        en/
            about/
            contact/
        fr/
            about/
            contact/


The root page
=============

The root page (``/``) should detect the browsers language and forward them to the correct language homepage (``/en/``, ``/fr/``). This page should sit at the site root (where the homepage would normally be).

We must set Django's ``LANGUAGES`` setting so we don't redirect non English/French users to pages that don't exist.


.. code-block:: python

    # settings.py
    LANGUAGES = (
        ('en', _("English")),
        ('fr', _("French")),
    )

    # models.py
    from django.utils import translation
    from django.http import HttpResponseRedirect

    from wagtail.wagtailcore.models import Page


    class LanguageRedirectionPage(Page):

        def serve(self, request):
            # This will only return a language that is in the LANGUAGES Django setting
            language = translation.get_language_from_request(request)

            return HttpResponseRedirect(self.url + language + '/')


Linking pages together
======================

It may be useful to link different versions of the same page together to allow the user to easily switch between languages. But we don't want to increase the burden on the editor too much so ideally, editors should only need to link one of the pages to the other versions and the links between the other versions should be created implicitly.

As this behaviour needs to be added to all page types that would be translated, its best to put this behaviour in a mixin.

Here's an example of how this could be implemented (with English as the main language and French/Spanish as alternative languages):

.. code-block:: python

    from wagtail.wagtailcore.models import Page
    from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, PageChooserPanel


    class TranslatablePageMixin(models.Model):
        # One link for each alternative language
        # These should only be used on the main language page (english)
        french_link = models.ForeignKey(Page, null=True, on_delete=models.SET_NULL, blank=True, related_name='+')
        spanish_link = models.ForeignKey(Page, null=True, on_delete=models.SET_NULL, blank=True, related_name='+')

        panels = [
            PageChooserPanel('french_link'),
            PageChooserPanel('spanish_link'),
        ]

        def get_language(self):
            """
            This returns the language code for this page.
            """
            # Look through ancestors of this page for its language homepage
            # The language homepage is located at depth 3
            language_homepage = self.get_ancestors(inclusive=True).get(depth=3)

            # The slug of language homepages should always be set to the language code
            return language_homepage.slug


        # Method to find the main language version of this page
        # This works by reversing the above links

        def english_page(self):
            """
            This finds the english version of this page
            """
            language = self.get_language()

            if language == 'en':
                return self
            elif language == 'fr':
                return type(self).objects.filter(french_link=self).first().specific
            elif language == 'es':
                return type(self).objects.filter(spanish_link=self).first().specific


        # We need a method to find a version of this page for each alternative language.
        # These all work the same way. They firstly find the main version of the page
        # (english), then from there they can just follow the link to the correct page.

        def french_page(self):
            """
            This finds the french version of this page
            """
            english_page = self.english_page()

            if english_page and english_page.french_link:
                return english_page.french_link.specific

        def spanish_page(self):
            """
            This finds the spanish version of this page
            """
            english_page = self.english_page()

            if english_page and english_page.spanish_link:
                return english_page.spanish_link.specific

        class Meta:
            abstract = True


    class AboutPage(Page, TranslatablePageMixin):
        ...
        content_panels = [
            ...
            MultiFieldPanel(TranslatablePageMixin.panels, 'Language links')
        ]


    class ContactPage(Page, TranslatablePageMixin):
        ...
        content_panels = [
            ...
            MultiFieldPanel(TranslatablePageMixin.panels, 'Language links')
        ]


You can make use of these methods in your template by doing:

.. code-block:: html+django

    {% if page.english_page and page.get_language != 'en' %}
        <a href="{{ page.english_page.url }}">{% trans "View in English" %}</a>
    {% endif %}

    {% if page.french_page and page.get_language != 'fr' %}
        <a href="{{ page.french_page.url }}">{% trans "View in French" %}</a>
    {% endif %}

    {% if page.spanish_page and page.get_language != 'es' %}
        <a href="{{ page.spanish_page.url }}">{% trans "View in Spanish" %}</a>
    {% endif %}
