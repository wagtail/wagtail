from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils


class AdminAPITestCase(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
