from django.http import HttpRequest
from django.template import Context, RequestContext, Template, engines
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.models import Site
from wagtail.test.utils import WagtailTestUtils

from .base import TranslatableSiteSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "other"])
class TemplateTestCase(TranslatableSiteSettingsTestMixin, TestCase, WagtailTestUtils):
    def render(self, request, string, context=None, site=None):
        template = Template(string)
        context = RequestContext(request, context)
        return template.render(context)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestContextProcessor(TemplateTestCase):
    def test_accessing_setting(self):
        """Check that the context processor works"""
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(locale=locale)
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.TesttranslatablesiteSetting.title }}",
                    ),
                    settings.title,
                )

    def test_multi_site(self):
        """Check that the correct setting for the current site is returned"""
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.default_site, locale=locale)
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.TesttranslatablesiteSetting.title }}",
                    ),
                    settings.title,
                )

        for locale, settings in [
            (None, self.other_settings),
            (self.fr_locale, self.other_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.other_site, locale=locale)
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.TesttranslatablesiteSetting.title }}",
                    ),
                    settings.title,
                )

    def test_model_case_insensitive(self):
        """Model names should be case insensitive"""
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(locale=locale)
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.testtranslatablesitesetting.title }}",
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.TESTtranslatablesITESETTING.title }}",
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.TesttranslatablesiteSetting.title }}",
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        request,
                        "{{ settings.tests.tEsttranslatablesiTesEttIng.title }}",
                    ),
                    settings.title,
                )

    def test_models_cached(self):
        """Accessing a setting should only hit the DB once per request instance and per locale,
        even if using that request to rendering multiple times"""
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(locale=locale)
                get_title = "{{ settings.tests.testtranslatablesitesetting.title }}"

                # force site query beforehand
                Site.find_for_request(request)

                with self.assertNumQueries(2):
                    for i in range(1, 4):
                        with self.subTest(attempt=i):
                            self.assertEqual(
                                self.render(request, get_title * i),
                                settings.title * i,
                            )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTemplateTag(TemplateTestCase):
    def test_no_context_processor(self):
        """
        Assert that not running the context processor means settings are not in
        the context, as expected.
        """
        template = Template("{{ settings.tests.TesttranslatablesiteSetting.title }}")
        context = Context()
        self.assertEqual(template.render(context), "")

    def test_get_settings_request_context(self):
        """Check that the {% get_settings %} tag works"""
        for locale, settings in [
            (None, self.other_settings),
            (self.fr_locale, self.other_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.other_site, locale=locale)
                context = Context({"request": request})

                # This should use the site in the request
                template = Template(
                    "{% load wagtailsettings_tags %}"
                    "{% get_settings %}"
                    "{{ settings.tests.testtranslatablesitesetting.title }}"
                )

                self.assertEqual(template.render(context), settings.title)

    def test_get_settings_request_context_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option
        overrides a request in the context, in which case the default
        locale is used.
        """
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.other_site, locale=locale)
                context = Context({"request": request})

                # This should use the default site, ignoring the site in the request
                template = Template(
                    "{% load wagtailsettings_tags %}"
                    "{% get_settings use_default_site=True %}"
                    "{{ settings.tests.testtranslatablesitesetting.title }}"
                )

                self.assertEqual(template.render(context), settings.title)

    def test_get_settings_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option works
        """
        context = Context()

        # This should use the default site
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings use_default_site=True %}"
            "{{ settings.tests.testtranslatablesitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)

    def test_get_settings_no_request_no_default(self):
        """
        Check that the {% get_settings %} throws an error if it can not find a
        site to work with
        """
        context = Context()

        # Without a request in the context, and without use_default_site, this
        # should bail with an error
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings %}"
            "{{ settings.tests.testtranslatablesitesetting.title }}"
        )
        with self.assertRaises(RuntimeError):
            template.render(context)

    def test_get_settings_variable_assignment_request_context(self):
        """
        Check that assigning the setting to a context variable with
        {% get_settings as wagtail_settings %} works.
        """
        for locale, settings in [
            (None, self.other_settings),
            (self.fr_locale, self.other_settings_fr),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.other_site, locale=locale)
                context = Context({"request": request})
                template = Template(
                    "{% load wagtailsettings_tags %}"
                    "{% get_settings as wagtail_settings %}"
                    "{{ wagtail_settings.tests.testtranslatablesitesetting.title }}"
                )
                self.assertEqual(template.render(context), settings.title)

                # Also check that the default 'settings' variable hasn't been set
                template = Template(
                    "{% load wagtailsettings_tags %}"
                    "{% get_settings as wagtail_settings %}"
                    "{{ settings.tests.testtranslatablesitesetting.title }}"
                )
                self.assertEqual(template.render(context), "")

    def test_get_settings_variable_assigment_use_default(self):
        """
        Check that assigning the setting to a context variable with
        {% get_settings use_default_site=True as wagtail_settings %} works.
        """
        context = Context()
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings use_default_site=True as wagtail_settings %}"
            "{{ wagtail_settings.tests.testtranslatablesitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableSiteSettingsJinja(TemplateTestCase):
    def setUp(self):
        super().setUp()
        self.engine = engines["jinja2"]

    def render(self, string, context=None, request_context=True, locale=None):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
            if "site" in context:
                site = context["site"]
            else:
                site = Site.objects.get(is_default_site=True)
            request = HttpRequest()
            request.META["HTTP_HOST"] = site.hostname
            request.META["SERVER_PORT"] = site.port

            if locale:
                request.GET["locale"] = locale.language_code

            context["request"] = request

        template = self.engine.from_string(string)
        return template.render(context)

    def test_accessing_setting(self):
        self.assertEqual(
            self.render('{{ settings("tests.TestTranslatableSiteSetting").title }}'),
            self.default_settings.title,
        )

    def test_multi_site(self):
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings),
        ]:
            with self.subTest(locale=locale):
                context = {"site": self.default_site}
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.TestTranslatableSiteSetting").title }}',
                        context,
                        locale=locale,
                    ),
                    settings.title,
                )

        for locale, settings in [
            (None, self.other_settings),
            (self.fr_locale, self.other_settings),
        ]:
            with self.subTest(locale=locale):
                context = {"site": self.other_site}
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.TestTranslatableSiteSetting").title }}',
                        context,
                        locale=locale,
                    ),
                    settings.title,
                )

    def test_model_case_insensitive(self):
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings),
        ]:
            with self.subTest(locale=locale):
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.testTranslatablesitesetting").title }}',
                        locale=locale,
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.TESTTranslatableSITESETTING").title }}',
                        locale=locale,
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.TestTranslatableSiteSetting").title }}',
                        locale=locale,
                    ),
                    settings.title,
                )
                self.assertEqual(
                    self.render(
                        '{{ settings("tests.tEstTranslatableSiTesEttIng").title }}',
                        locale=locale,
                    ),
                    settings.title,
                )

    def test_models_cached(self):
        get_title = '{{ settings("tests.testTranslatablesitesetting").title }}'

        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(locale=locale)
                # run extra query before hand
                Site.find_for_request(request)

                for i in range(1, 4):
                    with self.assertNumQueries(2):
                        context = {"request": request}
                        template = self.engine.from_string(get_title * i)
                        self.assertEqual(template.render(context), settings.title * i)

    def test_settings_use_default_site_override(self):
        for locale, settings in [
            (None, self.default_settings),
            (self.fr_locale, self.default_settings),
        ]:
            with self.subTest(locale=locale):
                request = self.get_request(site=self.other_site, locale=locale)
                context = {"request": request}

                # This should use the default site, ignoring the site in the request
                template = '{{ settings("tests.testTranslatablesitesetting", use_default_site=True).title }}'

                self.assertEqual(self.render(template, context), settings.title)

    def test_settings_use_default_site(self):
        context = {}

        # This should use the default site
        template = '{{ settings("tests.testTranslatablesitesetting", use_default_site=True).title }}'

        self.assertEqual(
            self.render(template, context, request_context=False),
            self.default_settings.title,
        )

    def test_settings_no_request_no_use_default(self):
        context = {}

        # Without a request in the context, and without use_default_site, this
        # should bail with an error
        template = '{{ settings("tests.testTranslatablesitesetting").title }}'
        with self.assertRaises(RuntimeError):
            self.render(template, context, request_context=False)
