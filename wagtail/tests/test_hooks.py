from unittest import mock

from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from wagtail import hooks
from wagtail.models import Page, PageViewRestriction
from wagtail.test.utils import WagtailTestUtils
from wagtail.views import serve, serve_chain
from wagtail.wagtail_hooks import check_view_restrictions


def test_hook():
    pass


class TestLoginView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpClass(cls):
        hooks.register("test_hook_name", test_hook)

    @classmethod
    def tearDownClass(cls):
        del hooks._hooks["test_hook_name"]

    def test_before_hook(self):
        def before_hook():
            pass

        with self.register_hook("test_hook_name", before_hook, order=-1):
            hook_fns = hooks.get_hooks("test_hook_name")
            self.assertEqual(hook_fns, [before_hook, test_hook])

    def test_after_hook(self):
        def after_hook():
            pass

        with self.register_hook("test_hook_name", after_hook, order=1):
            hook_fns = hooks.get_hooks("test_hook_name")
            self.assertEqual(hook_fns, [test_hook, after_hook])


class TestServeHooks(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.page = Page.objects.get(id=2)
        self.request = RequestFactory().get("/test/")
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(self.request)
        self.request.session.save()

    def test_serve_chain_order(self):
        order_calls = []

        def hook_1(next_fn):
            def wrapper(page, request, *args, **kwargs):
                order_calls.append(1)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        def hook_2(next_fn):
            def wrapper(page, request, *args, **kwargs):
                order_calls.append(2)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        def hook_3(next_fn):
            def wrapper(page, request, *args, **kwargs):
                order_calls.append(3)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        with self.register_hook("on_serve_page", hook_1):
            with self.register_hook("on_serve_page", hook_2):
                with self.register_hook("on_serve_page", hook_3):
                    serve(self.request, self.page.url)

                    self.assertEqual(order_calls, [1, 2, 3])

    def test_serve_chain_modification(self):
        def hook_modifier(next_fn):
            def wrapper(page, request, *args, **kwargs):
                response = next_fn(page, request, *args, **kwargs)
                response.content = b"Modified content"
                return response

            return wrapper

        with self.register_hook("on_serve_page", hook_modifier):
            response = serve(self.request, self.page.url)
            self.assertEqual(response.content, b"Modified content")

    def test_serve_chain_halt_execution(self):
        def hook_halt(next_fn):
            def wrapper(page, request, *args, **kwargs):
                return HttpResponse("Halted")

            return wrapper

        with self.register_hook("on_serve_page", hook_halt):
            response = serve(self.request, self.page.url)
            self.assertEqual(response.content, b"Halted")

    def test_serve_chain_view_restriction(self):
        restriction = PageViewRestriction.objects.create(
            page=self.page,
            restriction_type=PageViewRestriction.PASSWORD,
            password="password",
        )

        with self.register_hook("on_serve_page", check_view_restrictions):
            response = self.client.get(self.page.url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "wagtailcore/password_required.html")

        restriction.delete()

    def test_serve_always_called_last(self):
        hook_calls = []
        serve_called = []

        def hook_1(next_fn):
            def wrapper(page, request, *args, **kwargs):
                hook_calls.append(1)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        def hook_2(next_fn):
            def wrapper(page, request, *args, **kwargs):
                hook_calls.append(2)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        def hook_3(next_fn):
            def wrapper(page, request, *args, **kwargs):
                hook_calls.append(3)
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        original_serve_chain = serve_chain

        def mock_serve_chain(page, request, *args, **kwargs):
            serve_called.append(True)
            return original_serve_chain(page, request, *args, **kwargs)

        with mock.patch("wagtail.views.serve_chain", mock_serve_chain):
            with self.register_hook("on_serve_page", hook_1):
                with self.register_hook("on_serve_page", hook_2):
                    with self.register_hook("on_serve_page", hook_3):
                        serve(self.request, self.page.url)

                        self.assertEqual(hook_calls, [1, 2, 3])
                        self.assertEqual(len(serve_called), 1)
                        self.assertTrue(serve_called[0])

    def test_check_view_restrictions_receives_correct_parameters(self):
        received_params = []

        def hook_spy(next_fn):
            def wrapper(page, request, *args, **kwargs):
                received_params.append(
                    {"page": page, "request": request, "args": args, "kwargs": kwargs}
                )
                return next_fn(page, request, *args, **kwargs)

            return wrapper

        self.assertIsNotNone(self.page, "Test page should not be None")
        self.assertIsNotNone(self.request, "Test request should not be None")

        with self.register_hook("on_serve_page", hook_spy):
            route_result = Page.route_for_request(self.request, self.page.url)

            self.assertIsNotNone(route_result, "route_result should not be None")

            if route_result:
                page, args, kwargs = route_result
                serve(self.request, self.page.url)

                self.assertEqual(len(received_params), 1)

                params = received_params[0]

                self.assertIsNotNone(params["page"], "Hook received None as page")
                self.assertIsNotNone(params["request"], "Hook received None as request")

                self.assertEqual(params["page"], self.page)
                self.assertEqual(params["request"], self.request)

                self.assertEqual(params["args"], ([], {}))
                self.assertEqual(params["kwargs"], {})
