from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import resolve
from django.conf.urls import url

from wagtail.wagtailadmin.modules.base import Module, module_view


class TestBaseModule(TestCase):
    def test_init(self):
        module = Module('modulename', testattr="Hello world!")

        self.assertEqual(module.namespace, "modulename")
        self.assertEqual(module.testattr, "Hello world!")

    def test_has_module_permission(self):
        module = Module('modulename')

        request = RequestFactory().get('/')
        self.assertTrue(module.has_module_permission(request))

    def test_urls(self):
        module = Module('modulename')

        self.assertEqual(module.urls[1], 'modulename')
        self.assertEqual(module.urls[2], '')

    def test_request_module_attribute(self):
        view_called = [False]
        assertEqual = self.assertEqual

        class MyModule(Module):
            def test_view(self, request):
                view_called[0] = True

                # Module should be passed through on request object
                assertEqual(request.module, module)

            def get_urls(self):
                return (
                    url(r'^$', self.test_view, name='index'),
                )

        module = MyModule('test')
        view, args, kwargs = resolve('/', module.urls[0])

        request = RequestFactory().get('/')
        view(request, *args, **kwargs)

        self.assertTrue(view_called[0])


class TestModuleViewDecorator(TestCase):
    def test_module_view_decorator(self):
        @module_view
        def view(module, request, myarg, mykwarg=None):
            self.assertEqual(module, "Module")
            self.assertEqual(myarg, "Hello")
            self.assertEqual(mykwarg, "World")

        request = RequestFactory().get('/')
        request.module = "Module"
        view(request, "Hello", mykwarg="World")
