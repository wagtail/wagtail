from django.test import TestCase

from wagtail.test.utils import WagtailTestUtils


class AdminAPITestCase(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
