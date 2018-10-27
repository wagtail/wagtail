import os

from django.conf import settings
from django.core import serializers
from django.template import engines
from django.test import TestCase

from wagtail.core.models import Site

from .utils import Image, get_test_image_file


class TestImagesJinja(TestCase):

    def setUp(self):
        self.engine = engines['jinja2']

        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Create an image with a missing file, by deserializing fom a python object
        # (which bypasses FileField's attempt to read the file)
        self.bad_image = list(serializers.deserialize('python', [{
            'fields': {
                'title': 'missing image',
                'height': 100,
                'file': 'original_images/missing-image.jpg',
                'width': 100,
            },
            'model': 'wagtailimages.image'
        }]))[0].object
        self.bad_image.save()

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
            self.render('{{ image(myimage, "width-200", alt="alternate", class="test") }}', {'myimage': self.image}),
            '<img alt="alternate" src="{}" width="200" height="150" class="test">'.format(
                self.get_image_filename(self.image, "width-200")))

    def test_image_assignment(self):
        template = ('{% set background=image(myimage, "width-200") %}'
                    'width: {{ background.width }}, url: {{ background.url }}')
        output = ('width: 200, url: ' + self.get_image_filename(self.image, "width-200"))
        self.assertHTMLEqual(self.render(template, {'myimage': self.image}), output)

    def test_missing_image(self):
        self.assertHTMLEqual(
            self.render('{{ image(myimage, "width-200") }}', {'myimage': self.bad_image}),
            '<img alt="missing image" src="/media/not-found" width="0" height="0">'
        )

    def test_image_url(self):
        self.assertRegex(
            self.render('{{ image_url(myimage, "width-200") }}', {'myimage': self.image}),
            '/images/.*/width-200/{}'.format(self.image.file.name.split('/')[-1]),
        )

    def test_image_url_custom_view(self):
        self.assertRegex(
            self.render('{{ image_url(myimage, "width-200", "wagtailimages_serve_custom_view") }}', {'myimage': self.image}),
            '/testimages/custom_view/.*/width-200/{}'.format(self.image.file.name.split('/')[-1]),
        )
