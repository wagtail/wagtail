from django.http import HttpRequest
from django.template import Context, RequestContext, Template, engines
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.models import Site
from wagtail.test.utils import WagtailTestUtils

from .base import SiteSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "other"])
class TemplateTestCase(SiteSettingsTestMixin, TestCase, WagtailTestUtils):
    def render(self, request, string, context=None, site=None):
        template = Template(string)
        context = RequestContext(request, context)
        return template.render(context)


class TestContextProcessor(TemplateTestCase):
    def test_accessing_setting(self):
        """Check that the context processor works"""
        request = self.get_request()
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestSiteSetting.title }}"),
            self.default_settings.title,
        )

    def test_multisite(self):
        """Check that the correct setting for the current site is returned"""
        request = self.get_request(site=self.default_site)
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestSiteSetting.title }}"),
            self.default_settings.title,
        )

        request = self.get_request(site=self.other_site)
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestSiteSetting.title }}"),
            self.other_settings.title,
        )

    def test_model_case_insensitive(self):
        """Model names should be case insensitive"""
        request = self.get_request()
        self.assertEqual(
            self.render(request, "{{ settings.tests.testsitesetting.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.TESTSITESETTING.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestSiteSetting.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.tEstSiTesEttIng.title }}"),
            self.default_settings.title,
        )

    def test_models_cached(self):
        """Accessing a setting should only hit the DB once per request instance,
        even if using that request to rendering multiple times"""
        request = self.get_request()
        get_title = "{{ settings.tests.testsitesetting.title }}"

        # force site query beforehand
        Site.find_for_request(request)

        with self.assertNumQueries(1):
            for i in range(1, 4):
                with self.subTest(attempt=i):
                    self.assertEqual(
                        self.render(request, get_title * i),
                        self.default_settings.title * i,
                    )


class TestTemplateTag(TemplateTestCase):
    def test_no_context_processor(self):
        """
        Assert that not running the context processor means settings are not in
        the context, as expected.
        """
        template = Template("{{ settings.tests.TestSiteSetting.title }}")
        context = Context()
        self.assertEqual(template.render(context), "")

    def test_get_settings_request_context(self):
        """Check that the {% get_settings %} tag works"""
        request = self.get_request(site=self.other_site)
        context = Context({"request": request})

        # This should use the site in the request
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings %}"
            "{{ settings.tests.testsitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.other_settings.title)

    def test_get_settings_request_context_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option
        overrides a request in the context.
        """
        request = self.get_request(site=self.other_site)
        context = Context({"request": request})

        # This should use the default site, ignoring the site in the request
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings use_default_site=True %}"
            "{{ settings.tests.testsitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)

    def test_get_settings_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option works
        """
        context = Context()

        # This should use the default site
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings use_default_site=True %}"
            "{{ settings.tests.testsitesetting.title }}"
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
            "{{ settings.tests.testsitesetting.title }}"
        )
        with self.assertRaises(RuntimeError):
            template.render(context)

    def test_get_settings_variable_assignment_request_context(self):
        """
        Check that assigning the setting to a context variable with
        {% get_settings as wagtail_settings %} works.
        """
        request = self.get_request(site=self.other_site)
        context = Context({"request": request})
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings as wagtail_settings %}"
            "{{ wagtail_settings.tests.testsitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.other_settings.title)
        # Also check that the default 'settings' variable hasn't been set
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings as wagtail_settings %}"
            "{{ settings.tests.testsitesetting.title }}"
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
            "{{ wagtail_settings.tests.testsitesetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)


class TestSiteSettingsJinja(TemplateTestCase):
    def setUp(self):
        super().setUp()
        self.engine = engines["jinja2"]

    def render(self, string, context=None, request_context=True):
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
            context["request"] = request

        template = self.engine.from_string(string)
        return template.render(context)

    def test_accessing_setting(self):
        """Check that the context processor works"""
        self.assertEqual(
            self.render('{{ settings("tests.TestSiteSetting").title }}'),
            self.default_settings.title,
        )

    def test_multisite(self):
        """Check that the correct setting for the current site is returned"""
        context = {"site": self.default_site}
        self.assertEqual(
            self.render(
                '{{ settings("tests.TestSiteSetting").title }}',
                context,
            ),
            self.default_settings.title,
        )

        context = {"site": self.other_site}
        self.assertEqual(
            self.render(
                '{{ settings("tests.TestSiteSetting").title }}',
                context,
            ),
            self.other_settings.title,
        )

    def test_model_case_insensitive(self):
        """Model names should be case insensitive"""
        self.assertEqual(
            self.render('{{ settings("tests.testsitesetting").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.TESTSITESETTING").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.TestSiteSetting").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.tEstSiTesEttIng").title }}'),
            self.default_settings.title,
        )

    def test_models_cached(self):
        """Accessing a setting should only hit the DB once per render"""
        get_title = '{{ settings("tests.testsitesetting").title }}'

        request = self.get_request()
        # run extra query before hand
        Site.find_for_request(request)

        for i in range(1, 4):
            with self.assertNumQueries(1):
                context = {"request": request}
                template = self.engine.from_string(get_title * i)
                self.assertEqual(
                    template.render(context), self.default_settings.title * i
                )

    def test_settings_use_default_site_override(self):
        """
        Check that {{ settings(use_default_site=True) }} overrides a site in
        the context.
        """
        request = self.get_request(site=self.other_site)
        context = {"request": request}

        # This should use the default site, ignoring the site in the request
        template = (
            '{{ settings("tests.testsitesetting", use_default_site=True).title }}'
        )

        self.assertEqual(self.render(template, context), self.default_settings.title)

    def test_settings_use_default_site(self):
        """
        Check that the {{ settings(use_default_site=True) }} option works with
        no site in the context
        """
        context = {}

        # This should use the default site
        template = (
            '{{ settings("tests.testsitesetting", use_default_site=True).title }}'
        )

        self.assertEqual(
            self.render(template, context, request_context=False),
            self.default_settings.title,
        )

    def test_settings_no_request_no_use_default(self):
        """
        Check that {{ settings }} throws an error if it can not find a
        site to work with
        """
        context = {}

        # Without a request in the context, and without use_default_site, this
        # should bail with an error
        template = '{{ settings("tests.testsitesetting").title }}'
        with self.assertRaises(RuntimeError):
            self.render(template, context, request_context=False)
