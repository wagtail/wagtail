from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils


class AdminAPITestCase(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
