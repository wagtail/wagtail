from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore import hooks


def test_hook():
    pass


class TestLoginView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    @classmethod
    def setUpClass(cls):
        hooks.register('test_hook_name', test_hook)

    @classmethod
    def tearDownClass(cls):
        del hooks._hooks['test_hook_name']

    def test_before_hook(self):
        def before_hook():
            pass

        with self.register_hook('test_hook_name', before_hook, order=-1):
            hook_fns = hooks.get_hooks('test_hook_name')
            self.assertEqual(hook_fns, [before_hook, test_hook])

    def test_after_hook(self):
        def after_hook():
            pass

        with self.register_hook('test_hook_name', after_hook, order=1):
            hook_fns = hooks.get_hooks('test_hook_name')
            self.assertEqual(hook_fns, [test_hook, after_hook])
