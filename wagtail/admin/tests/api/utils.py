from django.test import TransactionTestCase, tag

from wagtail.test.utils import WagtailTestUtils


@tag("transaction")
class AdminAPITestCase(WagtailTestUtils, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.login()
