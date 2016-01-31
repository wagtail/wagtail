from django.test import TestCase
from wagtail.wagtailcore.fields import BaseTextAreaWidget


class TestBaseTextAreaWidget(TestCase):

    def test_is_abstract(self):
        import ipdb; ipdb.set_trace()
        with self.assertRaises(NotImplementedError):
            fail = BaseTextAreaWidget()
            fail.get_panel()


