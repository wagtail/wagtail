from django.template import Context, RequestContext, Template, engines
from django.test import TestCase

from wagtail.core.models import Page, Site
from wagtail.tests.testapp.models import TestSetting
from wagtail.tests.utils import WagtailTestUtils


class TemplateTestCase(TestCase, WagtailTestUtils):
    def setUp(self):
        root = Page.objects.first()
        other_home = Page(title='Other Root')
        root.add_child(instance=other_home)

        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(hostname='other', root_page=other_home)

        self.test_setting = TestSetting.objects.create(
            title='Site title',
            email='initial@example.com',
            site=self.default_site)

        self.other_setting = TestSetting.objects.create(
            title='Other title',
            email='other@example.com',
            site=self.other_site)

    def get_request(self, site=None):
        if site is None:
            site = self.default_site
        request = self.client.get('/test/', HTTP_HOST=site.hostname)
        request.site = site
        return request

    def render(self, request, string, context=None, site=None):
        template = Template(string)
        context = RequestContext(request, context)
        return template.render(context)


class TestContextProcessor(TemplateTestCase):

    def test_accessing_setting(self):
        """ Check that the context processor works """
        request = self.get_request()
        self.assertEqual(
            self.render(request, '{{ settings.tests.TestSetting.title }}'),
            self.test_setting.title)

    def test_multisite(self):
        """ Check that the correct setting for the current site is returned """
        request = self.get_request(site=self.default_site)
        self.assertEqual(
            self.render(request, '{{ settings.tests.TestSetting.title }}'),
            self.test_setting.title)

        request = self.get_request(site=self.other_site)
        self.assertEqual(
            self.render(request, '{{ settings.tests.TestSetting.title }}'),
            self.other_setting.title)

    def test_model_case_insensitive(self):
        """ Model names should be case insensitive """
        request = self.get_request()
        self.assertEqual(
            self.render(request, '{{ settings.tests.testsetting.title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render(request, '{{ settings.tests.TESTSETTING.title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render(request, '{{ settings.tests.TestSetting.title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render(request, '{{ settings.tests.tEstsEttIng.title }}'),
            self.test_setting.title)

    def test_models_cached(self):
        """ Accessing a setting should only hit the DB once per render """
        request = self.get_request()
        get_title = '{{ settings.tests.testsetting.title }}'

        for i in range(1, 4):
            with self.assertNumQueries(1):
                self.assertEqual(
                    self.render(request, get_title * i),
                    self.test_setting.title * i)


class TestTemplateTag(TemplateTestCase):
    def test_no_context_processor(self):
        """
        Assert that not running the context processor means settings are not in
        the context, as expected.
        """
        template = Template('{{ settings.tests.TestSetting.title }}')
        context = Context()
        self.assertEqual(template.render(context), '')

    def test_get_settings_request_context(self):
        """ Check that the {% get_settings %} tag works """
        request = self.get_request(site=self.other_site)
        context = Context({'request': request})

        # This should use the site in the request
        template = Template('{% load wagtailsettings_tags %}'
                            '{% get_settings %}'
                            '{{ settings.tests.testsetting.title}}')

        self.assertEqual(template.render(context), self.other_setting.title)

    def test_get_settings_request_context_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option
        overrides a request in the context.
        """
        request = self.get_request(site=self.other_site)
        context = Context({'request': request})

        # This should use the default site, ignoring the site in the request
        template = Template('{% load wagtailsettings_tags %}'
                            '{% get_settings use_default_site=True %}'
                            '{{ settings.tests.testsetting.title}}')

        self.assertEqual(template.render(context), self.test_setting.title)

    def test_get_settings_use_default(self):
        """
        Check that the {% get_settings use_default_site=True %} option works
        """
        context = Context()

        # This should use the default site
        template = Template('{% load wagtailsettings_tags %}'
                            '{% get_settings use_default_site=True %}'
                            '{{ settings.tests.testsetting.title}}')

        self.assertEqual(template.render(context), self.test_setting.title)

    def test_get_settings_no_request_no_default(self):
        """
        Check that the {% get_settings %} throws an error if it can not find a
        site to work with
        """
        context = Context()

        # Without a request in the context, and without use_default_site, this
        # should bail with an error
        template = Template('{% load wagtailsettings_tags %}'
                            '{% get_settings %}'
                            '{{ settings.tests.testsetting.title}}')
        with self.assertRaises(RuntimeError):
            template.render(context)


class TestSettingsJinja(TemplateTestCase):

    def setUp(self):
        super().setUp()
        self.engine = engines['jinja2']

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
            if 'site' in context:
                site = context['site']
            else:
                site = Site.objects.get(is_default_site=True)

            request = self.client.get('/test/', HTTP_HOST=site.hostname)
            request.site = site
            context['request'] = request

        template = self.engine.from_string(string)
        return template.render(context)

    def test_accessing_setting(self):
        """ Check that the context processor works """
        self.assertEqual(
            self.render('{{ settings("tests.TestSetting").title }}'),
            self.test_setting.title)

    def test_multisite(self):
        """ Check that the correct setting for the current site is returned """
        context = {'site': self.default_site}
        self.assertEqual(
            self.render('{{ settings("tests.TestSetting").title }}', context),
            self.test_setting.title)

        context = {'site': self.other_site}
        self.assertEqual(
            self.render('{{ settings("tests.TestSetting").title }}', context),
            self.other_setting.title)

    def test_model_case_insensitive(self):
        """ Model names should be case insensitive """
        self.assertEqual(
            self.render('{{ settings("tests.testsetting").title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render('{{ settings("tests.TESTSETTING").title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render('{{ settings("tests.TestSetting").title }}'),
            self.test_setting.title)
        self.assertEqual(
            self.render('{{ settings("tests.tEstsEttIng").title }}'),
            self.test_setting.title)

    def test_models_cached(self):
        """ Accessing a setting should only hit the DB once per render """
        get_title = '{{ settings("tests.testsetting").title }}'

        # Cant use the default 'self.render()' as it does DB queries to get
        # site, dummy request
        site = Site.objects.get(is_default_site=True)
        request = self.client.get('/test/', HTTP_HOST=site.hostname)
        request.site = site

        for i in range(1, 4):
            with self.assertNumQueries(1):
                context = {'request': request}
                template = self.engine.from_string(get_title * i)
                self.assertEqual(
                    template.render(context),
                    self.test_setting.title * i)

    def test_settings_use_default_site_override(self):
        """
        Check that {{ settings(use_default_site=True) }} overrides a site in
        the context.
        """
        request = self.get_request(site=self.other_site)
        context = {'request': request}

        # This should use the default site, ignoring the site in the request
        template = '{{ settings("tests.testsetting", use_default_site=True).title }}'

        self.assertEqual(
            self.render(template, context),
            self.test_setting.title)

    def test_settings_use_default_site(self):
        """
        Check that the {{ settings(use_default_site=True) }} option works with
        no site in the context
        """
        context = {}

        # This should use the default site
        template = '{{ settings("tests.testsetting", use_default_site=True).title}}'

        self.assertEqual(
            self.render(template, context, request_context=False),
            self.test_setting.title)

    def test_settings_no_request_no_use_default(self):
        """
        Check that {{ settings }} throws an error if it can not find a
        site to work with
        """
        context = {}

        # Without a request in the context, and without use_default_site, this
        # should bail with an error
        template = '{{ settings("tests.testsetting").title}}'
        with self.assertRaises(RuntimeError):
            self.render(template, context, request_context=False)
