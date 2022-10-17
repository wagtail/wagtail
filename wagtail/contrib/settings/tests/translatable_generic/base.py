from django.http import HttpRequest

from wagtail.models import Locale, Page, Site
from wagtail.test.testapp.models import TestTranslatableGenericSetting


class TranslatableGenericSettingsTestMixin:
    def setUp(self):
        root = Page.objects.first()
        other_root = Page(title="Other Root")
        root.add_child(instance=other_root)

        self.model = TestTranslatableGenericSetting

        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(hostname="other", root_page=other_root)

        self.en_locale = Locale.get_default()
        self.fr_locale = Locale.objects.create(language_code="fr")

        self.default_settings = TestTranslatableGenericSetting.objects.create(
            title="Default GenericSettings title",
            email="email@example.com",
            translation_key=TestTranslatableGenericSetting._translation_key,
        )
        self.default_settings_fr = self.default_settings.copy_for_translation(
            self.fr_locale
        )
        self.default_settings_fr.title = "Titre du site"
        self.default_settings_fr.email = "initial@exemple.com"
        self.default_settings_fr.save()

    def get_request(self, site=None, locale=None):
        if site is None:
            site = self.default_site
        request = HttpRequest()
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port
        if locale:
            request.GET["locale"] = locale.language_code
        return request
