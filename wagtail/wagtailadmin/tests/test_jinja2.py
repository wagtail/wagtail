from __future__ import absolute_import, unicode_literals


import unittest

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from wagtail.wagtailcore.models import Page, PAGE_TEMPLATE_VAR, Site


@unittest.skipIf(django.VERSION < (1, 8), 'Multiple engines only supported in Django>=1.8')
class TestCoreJinja(TestCase):

    def setUp(self):
        # This does not exist on Django<1.8
        from django.template import engines
        self.engine = engines['jinja2']

        self.user = get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')
        self.homepage = Page.objects.get(id=2)

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        template = self.engine.from_string(string)
        return template.render(context)

    def dummy_request(self, user=None):
        site = Site.objects.get(is_default_site=True)

        request = self.client.get('/')
        request.site = site
        request.user = user or AnonymousUser()
        return request

    def test_userbar(self):
        content = self.render('{{ wagtailuserbar() }}', {
            PAGE_TEMPLATE_VAR: self.homepage,
            'request': self.dummy_request(self.user)})
        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_anonymous_user(self):
        content = self.render('{{ wagtailuserbar() }}', {
            PAGE_TEMPLATE_VAR: self.homepage,
            'request': self.dummy_request()})

        # Make sure nothing was rendered
        self.assertEqual(content, '')
