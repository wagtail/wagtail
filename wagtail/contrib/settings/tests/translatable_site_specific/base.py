from django.http import HttpRequest

from wagtail.contrib.settings.models import BaseTranslatableSiteSetting
from wagtail.models import Locale, Page, Site
from wagtail.test.testapp.models import TestTranslatableSiteSetting


class TranslatableSiteSettingsTestMixin:
    def setUp(self):
        root = Page.objects.first()
        other_home = Page(title="Other Root")
        root.add_child(instance=other_home)

        self.en_locale = Locale.get_default()
        self.fr_locale = Locale.objects.create(language_code="fr")

        self.default_site = Site.objects.get(is_default_site=True)
        self.default_settings = TestTranslatableSiteSetting.objects.create(
            title="Site title",
            email="initial@example.com",
            site=self.default_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.default_site.id
            ),
        )
        self.default_settings_fr = self.default_settings.copy_for_translation(
            self.fr_locale
        )
        self.default_settings_fr.title = "Titre du site"
        self.default_settings_fr.email = "initial@exemple.com"
        self.default_settings_fr.save()

        self.other_site = Site.objects.create(hostname="other", root_page=other_home)
        self.other_settings = TestTranslatableSiteSetting.objects.create(
            title="Other title",
            email="other@other.com",
            site=self.other_site,
            translation_key=BaseTranslatableSiteSetting._get_translation_key(
                self.other_site.id
            ),
        )
        self.other_settings_fr = self.other_settings.copy_for_translation(
            self.fr_locale
        )
        self.other_settings_fr.title = "Autre titre"
        self.other_settings_fr.email = "autre@exemple.com"
        self.other_settings_fr.save()

    def get_request(self, site=None, locale=None):
        request = HttpRequest()

        if site is None:
            site = self.default_site
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port

        if locale:
            request.GET["locale"] = locale.language_code

        return request
