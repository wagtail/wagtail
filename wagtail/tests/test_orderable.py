from django.apps import apps
from django.core import checks
from django.test import TestCase

from wagtail.models import Orderable


class TestOrderable(TestCase):
    def tearDown(self):
        for model in ("orderablewithoutinheritance", "orderablewithoutsortorder"):
            try:
                del apps.all_models["wagtailcore"][model]
            except KeyError:
                pass
        apps.clear_cache()

    def test_raises_warning_if_meta_does_not_inherit_from_orderable(self):
        # class Meta should be inherited from Orderable
        class OrderableWithoutInheritance(Orderable):
            class Meta:
                app_label = "wagtailcore"
                verbose_name = "Orderable Without Inheritance"

        errors = OrderableWithoutInheritance.check()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Warning)
        self.assertEqual(errors[0].id, "wagtailcore.W002")

    def test_raises_warning_if_sort_order_not_in_meta_ordering(self):
        # for ordering the 'sort_order' should be defined
        class OrderableWithoutSortOrder(Orderable):
            class Meta(Orderable.Meta):
                app_label = "wagtailcore"
                ordering = []

        errors = OrderableWithoutSortOrder.check()

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Warning)
        self.assertEqual(errors[0].id, "wagtailcore.W003")
