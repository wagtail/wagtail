from __future__ import absolute_import, unicode_literals

import os
import unittest

import django
from django.conf import settings
from django.test import TestCase

from wagtail.wagtailcore.models import Site

from .utils import get_test_image_file, Image


@unittest.skipIf(django.VERSION < (1, 8), 'Multiple engines only supported in Django>=1.8')
class TestImagesJinja(TestCase):

    def setUp(self):
        # This does not exist on Django<1.8
        from django.template import engines
        self.engine = engines['jinja2']

        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def render(self, string, context=None, request_context=True):
        if context is None:
            context = {}

        # Add a request to the template, to simulate a RequestContext
        if request_context:
            site = Site.objects.get(is_default_site=True)
            request = self.client.get('/test/', HTTP_HOST=site.hostname)
            request.site = site
            context['request'] = request

        template = self.engine.from_string(string)
        return template.render(context)

    def get_image_filename(self, image, filterspec):
        """
        Get the generated filename for a resized image
        """
        name, ext = os.path.splitext(os.path.basename(image.file.name))
        return '{}images/{}.{}{}'.format(
            settings.MEDIA_URL, name, filterspec, ext)

    def test_image(self):
        self.assertHTMLEqual(
            self.render('{{ image(myimage, "width-200") }}', {'myimage': self.image}),
            '<img alt="Test image" src="{}" width="200" height="150">'.format(
                self.get_image_filename(self.image, "width-200")))

    def test_image_attributes(self):
        self.assertHTMLEqual(
            self.render('{{ image(myimage, "width-200", class="test") }}', {'myimage': self.image}),
            '<img alt="Test image" src="{}" width="200" height="150" class="test">'.format(
                self.get_image_filename(self.image, "width-200")))

    def test_image_assignment(self):
        template = ('{% set background=image(myimage, "width-200") %}'
                    'width: {{ background.width }}, url: {{ background.url }}')
        output = ('width: 200, url: ' + self.get_image_filename(self.image, "width-200"))
        self.assertHTMLEqual(self.render(template, {'myimage': self.image}), output)
