from django.http import HttpRequest
from django.template import Context, RequestContext, Template, engines
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.models import Site
from wagtail.test.utils import WagtailTestUtils

from .base import GenericSettingsTestMixin


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "other"])
class GenericSettingTemplateTestCase(
    GenericSettingsTestMixin, TestCase, WagtailTestUtils
):
    def render(self, request, string, context=None):
        template = Template(string)
        context = RequestContext(request, context)
        return template.render(context)


class GenericSettingContextProcessorTestCase(GenericSettingTemplateTestCase):
    def test_accessing_setting(self):
        """Check that the context processor works"""
        request = self.get_request()
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestGenericSetting.title }}"),
            self.default_settings.title,
        )

    def test_model_case_insensitive(self):
        """Model names should be case insensitive"""
        request = self.get_request()
        self.assertEqual(
            self.render(request, "{{ settings.tests.testgenericsetting.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.TESTGENERICSETTING.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.TestGenericSetting.title }}"),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render(request, "{{ settings.tests.tEstgEnerICsEttIng.title }}"),
            self.default_settings.title,
        )

    def test_models_cached(self):
        """Accessing a setting should only hit the DB once per request instance,
        even if using that request to rendering multiple times"""
        request = self.get_request()
        get_title = "{{ settings.tests.testgenericsetting.title }}"

        # force site query beforehand
        Site.find_for_request(request)

        with self.assertNumQueries(1):
            for i in range(1, 4):
                with self.subTest(attempt=i):
                    self.assertEqual(
                        self.render(request, get_title * i),
                        self.default_settings.title * i,
                    )


class GenericSettingTemplateTagTestCase(GenericSettingTemplateTestCase):
    def test_no_context_processor(self):
        """
        Assert that not running the context processor means settings are not in
        the context, as expected.
        """
        template = Template("{{ settings.tests.TestGenericSetting.title }}")
        context = Context()
        self.assertEqual(template.render(context), "")

    def test_get_settings_request_context(self):
        """Check that the {% get_settings %} tag works"""
        request = self.get_request()
        context = Context({"request": request})

        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings %}"
            "{{ settings.tests.testgenericsetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)

    def test_get_settings_no_request(self):
        """Check that the {% get_settings %} tag works with no request"""
        context = Context()

        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings %}"
            "{{ settings.tests.testgenericsetting.title }}"
        )

        self.assertEqual(template.render(context), self.default_settings.title)

    def test_get_settings_variable_assignment_request_context(self):
        """
        Check that assigning the setting to a context variable with
        {% get_settings as wagtail_settings %} works.
        """
        request = self.get_request()
        context = Context({"request": request})
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings as wagtail_settings %}"
            "{{ wagtail_settings.tests.testgenericsetting.title }}"
        )
        self.assertEqual(template.render(context), self.default_settings.title)

        # Also check that the default 'settings' variable hasn't been set
        template = Template(
            "{% load wagtailsettings_tags %}"
            "{% get_settings as wagtail_settings %}"
            "{{ settings.tests.testgenericsetting.title }}"
        )
        self.assertEqual(template.render(context), "")


class GenericSettingJinjaContextProcessorTestCase(GenericSettingTemplateTestCase):
    def setUp(self):
        super().setUp()
        self.engine = engines["jinja2"]

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
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
            self.render('{{ settings("tests.TestGenericSetting").title }}'),
            self.default_settings.title,
        )

    def test_model_case_insensitive(self):
        """Model names should be case insensitive"""
        self.assertEqual(
            self.render('{{ settings("tests.testgenericsetting").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.TESTGENERICSETTING").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.TestGenericSetting").title }}'),
            self.default_settings.title,
        )
        self.assertEqual(
            self.render('{{ settings("tests.tEstgEnerICsEttIng").title }}'),
            self.default_settings.title,
        )

    def test_models_cached(self):
        """Accessing a setting should only hit the DB once per render"""
        get_title = '{{ settings("tests.testgenericsetting").title }}'

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

    def test_settings_no_request(self):
        """
        Check that {{ settings }} does not throw an error if it can not find a
        request to work with
        """
        context = {}
        template = '{{ settings("tests.testgenericsetting").title }}'

        self.assertEqual(
            self.render(template, context, request_context=False),
            self.default_settings.title,
        )
