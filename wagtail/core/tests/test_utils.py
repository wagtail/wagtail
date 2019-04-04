# -*- coding: utf-8 -*
from django.test import TestCase
from django.utils.text import slugify

from wagtail.core.models import Page
from wagtail.core.utils import (
    accepts_kwarg, cautious_slugify, get_content_type_for_model, get_content_types_for_models
)
from wagtail.tests.testapp.models import Advert, ProxyAdvert, SimplePage, SimpleProxyPage


class TestCautiousSlugify(TestCase):

    def test_behaves_same_as_slugify_for_latin_chars(self):
        test_cases = [
            ('', ''),
            ('???', ''),
            ('Hello world', 'hello-world'),
            ('Hello_world', 'hello_world'),
            ('Hellö wörld', 'hello-world'),
            ('Hello   world', 'hello-world'),
            ('   Hello world   ', 'hello-world'),
            ('Hello, world!', 'hello-world'),
            ('Hello*world', 'helloworld'),
            ('Hello☃world', 'helloworld'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(slugify(original), expected_result)
            self.assertEqual(cautious_slugify(original), expected_result)

    def test_escapes_non_latin_chars(self):
        test_cases = [
            ('Straßenbahn', 'straxdfenbahn'),
            ('Спорт!', 'u0421u043fu043eu0440u0442'),
            ('〔山脈〕', 'u5c71u8108'),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(cautious_slugify(original), expected_result)


class TestAcceptsKwarg(TestCase):
    def test_accepts_kwarg(self):
        def func_without_banana(apple, orange=42):
            pass

        def func_with_banana(apple, banana=42):
            pass

        def func_with_kwargs(apple, **kwargs):
            pass

        self.assertFalse(accepts_kwarg(func_without_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_banana, 'banana'))
        self.assertTrue(accepts_kwarg(func_with_kwargs, 'banana'))


class TestContentTypeGetting(TestCase):

    def setUp(self):
        # To aid with adding new pages
        root_page = Page.objects.get(id=2)

        # ContentType.get_for_model() and ContentType.get_for_models() both accept
        # model instances as well as classes, so the get_content_type_for_model()
        # and get_content_types_for_models() do too. For each 'category' of model,
        # we test with a model, and an instance of that model, to make sure the result
        # is consistent
        self.page_model = SimplePage
        self.page_model_instance = SimplePage(title='simple', content='page')
        root_page.add_child(instance=self.page_model_instance)

        self.page_proxy_model = SimpleProxyPage
        self.page_proxy_model_instance = SimpleProxyPage(title='simple proxy', content="page")
        root_page.add_child(instance=self.page_proxy_model_instance)

        self.non_page_model = Advert
        self.non_page_model_instance = Advert.objects.create(text='advert')
        self.non_page_proxy_model = ProxyAdvert
        self.non_page_proxy_model_instance = ProxyAdvert.objects.create(text='advert')

        # The following tuple defines the expected value of content_type.get_model()
        # when each of the above models/model instances are provided as an input to
        # get_content_type_for_model() or get_content_types_for_models()
        self.expected_content_type_models = (
            # the content type should be for same model
            (self.page_model, self.page_model),
            (self.page_model_instance, self.page_model),
            (self.page_proxy_model, self.page_proxy_model),
            (self.page_proxy_model_instance, self.page_proxy_model),
            (self.non_page_model, self.non_page_model),
            (self.non_page_model_instance, self.non_page_model),
            # the content type should be for the concrete model
            (self.non_page_proxy_model, self.non_page_model),
            (self.non_page_proxy_model_instance, self.non_page_model),
        )

    def test_get_content_type_for_model(self):
        for obj, expected_content_type_model in self.expected_content_type_models:
            content_type = get_content_type_for_model(obj)
            self.assertIs(content_type.model_class(), expected_content_type_model)

    def test_get_content_types_for_models(self):
        # `result` should be a dict mapping all inputs to their matched ContentType
        result = get_content_types_for_models(
            *[obj for obj, _ in self.expected_content_type_models]
        )
        for obj, expected_content_type_model in self.expected_content_type_models:
            content_type_model = result[obj].model_class()
            self.assertIs(content_type_model, expected_content_type_model)
