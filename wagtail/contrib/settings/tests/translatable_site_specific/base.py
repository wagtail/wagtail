from django.http import HttpRequest

from wagtail.contrib.settings.models import BaseTranslatableSiteSetting
from wagtail.models import Locale, Page, Site
from wagtail.test.testapp.models import TestTranslatableSiteSetting


class TranslatableSiteSettingsTestMixin:
    @classmethod
    def setUpTestData(cls):
        root = Page.objects.first()
        other_home = Page(title="Other Root")
        root.add_child(instance=other_home)

        cls.en_locale = Locale.get_default()
        cls.fr_locale = Locale.objects.create(language_code="fr")

        cls.default_site = Site.objects.get(is_default_site=True)
        cls.default_settings = TestTranslatableSiteSetting.objects.create(
            title="Site title",
            email="initial@example.com",
            site=cls.default_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                cls.default_site.id
            ),
        )
        cls.default_settings_fr = cls.default_settings.copy_for_translation(
            cls.fr_locale
        )
        cls.default_settings_fr.title = "Titre du site"
        cls.default_settings_fr.email = "initial@exemple.com"
        cls.default_settings_fr.save()

        cls.other_site = Site.objects.create(hostname="other", root_page=other_home)
        cls.other_settings = TestTranslatableSiteSetting.objects.create(
            title="Other title",
            email="other@other.com",
            site=cls.other_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                cls.other_site.id
            ),
        )
        cls.other_settings_fr = cls.other_settings.copy_for_translation(cls.fr_locale)
        cls.other_settings_fr.title = "Autre titre"
        cls.other_settings_fr.email = "autre@exemple.com"
        cls.other_settings_fr.save()

    def get_request(self, site=None, locale=None):
        request = HttpRequest()

        if site is None:
            site = self.default_site
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port

        if locale:
            request.GET["locale"] = locale.language_code

        return request
