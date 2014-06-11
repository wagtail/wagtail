from django.test import TestCase
from django.core.urlresolvers import reverse

from wagtail.tests.utils import login


class TestStyleGuide(TestCase):
    def setUp(self):
        login(self.client)

    def test_styleguide(self):
        response = self.client.get(reverse('wagtailstyleguide'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailstyleguide/base.html')
