from django.test import TransactionTestCase

from wagtail.test.utils import WagtailTestUtils


class AdminAPITestCase(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.login()
