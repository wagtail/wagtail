from unittest import mock

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.cache import has_vary_header, patch_vary_headers

from wagtail import hooks
from wagtail.models import PageViewRestriction, Site
from wagtail.test.routablepage.models import RoutablePageTest
from wagtail.test.testapp.models import EventIndex, EventPage, SimplePage
from wagtail.test.utils import Page, PageFixturesMixin

MARKDOWN_TYPES = ["text/html", "text/markdown"]


def serve_with_markdown(page, request, *args, **kwargs):
    """
    A serve() override that returns Markdown when the client prefers it,
    as a site would implement it.
    """
    if page.get_response_media_type(request) == "text/markdown":
        return HttpResponse(f"# {page.title}", content_type="text/markdown")
    return Page.serve(page, request, *args, **kwargs)


def vary_values(response):
    return [
        header.strip()
        for header in response.get("Vary", "").split(",")
        if header.strip()
    ]


class TestGetResponseMediaType(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def get_media_type(self, accept, media_types=MARKDOWN_TYPES):
        headers = {"accept": accept} if accept is not None else {}
        request = self.factory.get("/", headers=headers)
        page = SimplePage(title="Test")
        with mock.patch.object(SimplePage, "response_media_types", media_types):
            return page.get_response_media_type(request)

    def test_default_is_html(self):
        self.assertEqual(Page.response_media_types, ["text/html"])

    def test_single_media_type_ignores_accept(self):
        for accept in (None, "text/markdown", "application/json"):
            with self.subTest(accept=accept):
                self.assertEqual(
                    self.get_media_type(accept, media_types=["text/html"]),
                    "text/html",
                )

    def test_prefers_markdown(self):
        for accept in (
            "text/markdown",
            "text/markdown, text/html;q=0.9",
            "text/html;q=0.5, text/markdown",
            # The client's order breaks quality ties.
            "text/markdown, text/html",
            "text/markdown, */*;q=0.1",
        ):
            with self.subTest(accept=accept):
                self.assertEqual(self.get_media_type(accept), "text/markdown")

    def test_prefers_html(self):
        for accept in (
            None,
            "",
            "*/*",
            "text/*",
            # A typical browser Accept header.
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "text/html, text/markdown;q=0.5",
            "text/markdown;q=0, */*",
        ):
            with self.subTest(accept=accept):
                self.assertEqual(self.get_media_type(accept), "text/html")

    def test_falls_back_to_default_when_nothing_matches(self):
        for accept in ("application/json", "image/*", "text/markdown;q=0"):
            with self.subTest(accept=accept):
                self.assertEqual(self.get_media_type(accept), "text/html")

    def test_first_media_type_is_the_default(self):
        media_types = ["text/markdown", "text/html"]
        for accept in (None, "*/*", "text/*", "application/json"):
            with self.subTest(accept=accept):
                self.assertEqual(
                    self.get_media_type(accept, media_types=media_types),
                    "text/markdown",
                )
        self.assertEqual(
            self.get_media_type("text/html", media_types=media_types), "text/html"
        )

    def test_more_than_two_media_types(self):
        media_types = ["text/html", "text/markdown", "application/json"]
        self.assertEqual(
            self.get_media_type("application/json", media_types=media_types),
            "application/json",
        )
        self.assertEqual(
            self.get_media_type(
                "application/json;q=0.5, text/markdown", media_types=media_types
            ),
            "text/markdown",
        )


class TestGetVaryHeaders(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")

    def test_default(self):
        self.assertEqual(SimplePage().get_vary_headers(self.request), [])

    def test_multiple_media_types(self):
        with mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES):
            self.assertEqual(SimplePage().get_vary_headers(self.request), ["Accept"])


class TestServeVaryHeaders(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        Site.clear_site_root_paths_cache()

    def test_default_page_has_no_extra_vary_headers(self):
        response = self.client.get("/events/christmas/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(has_vary_header(response, "Accept"))
        self.assertFalse(has_vary_header(response, "X-Requested-With"))

    def test_default_page_ignores_accept(self):
        response = self.client.get(
            "/events/christmas/", headers={"accept": "text/markdown"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertFalse(has_vary_header(response, "Accept"))

    def test_existing_vary_headers_are_kept(self):
        # LocaleMiddleware adds Accept-Language in the test settings.
        with mock.patch.object(EventIndex, "response_media_types", MARKDOWN_TYPES):
            response = self.client.get("/events/")
        self.assertTrue(has_vary_header(response, "Accept-Language"))
        self.assertTrue(has_vary_header(response, "Accept"))

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    @mock.patch.object(SimplePage, "serve", serve_with_markdown)
    def test_negotiated_markdown(self):
        response = self.client.get("/about-us/", headers={"accept": "text/markdown"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown")
        self.assertEqual(response.content, b"# About us")
        self.assertTrue(has_vary_header(response, "Accept"))

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    @mock.patch.object(SimplePage, "serve", serve_with_markdown)
    def test_negotiated_html(self):
        for accept in (None, "*/*", "text/html"):
            with self.subTest(accept=accept):
                headers = {"accept": accept} if accept else {}
                response = self.client.get("/about-us/", headers=headers)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response["Content-Type"].startswith("text/html"))
                self.assertContains(response, "<h1>About us</h1>")
                # The HTML variant must vary too, or a cache would serve it
                # to clients that asked for Markdown.
                self.assertTrue(has_vary_header(response, "Accept"))

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    def test_vary_added_without_serve_override(self):
        response = self.client.get("/about-us/")
        self.assertTrue(has_vary_header(response, "Accept"))

    def test_vary_added_when_serve_returns_its_own_response(self):
        def serve(page, request, *args, **kwargs):
            return HttpResponse("custom")

        with (
            mock.patch.object(EventIndex, "serve", serve),
            mock.patch.object(EventIndex, "response_media_types", MARKDOWN_TYPES),
        ):
            response = self.client.get("/events/")
        self.assertEqual(response.content, b"custom")
        self.assertTrue(has_vary_header(response, "Accept"))

    def test_headers_are_not_duplicated(self):
        def serve(page, request, *args, **kwargs):
            response = HttpResponse("custom")
            patch_vary_headers(response, ["Accept", "X-Requested-With"])
            return response

        with (
            mock.patch.object(EventIndex, "serve", serve),
            mock.patch.object(EventIndex, "response_media_types", MARKDOWN_TYPES),
        ):
            response = self.client.get("/events/")
        values = [value.lower() for value in vary_values(response)]
        self.assertEqual(values.count("accept"), 1)
        self.assertEqual(values.count("x-requested-with"), 1)

    def test_custom_get_vary_headers(self):
        def get_vary_headers(page, request):
            return [*Page.get_vary_headers(page, request), "Cookie"]

        with mock.patch.object(SimplePage, "get_vary_headers", get_vary_headers):
            response = self.client.get("/about-us/")
        self.assertTrue(has_vary_header(response, "Cookie"))
        self.assertFalse(has_vary_header(response, "Accept"))

    def test_get_vary_headers_receives_the_request(self):
        with mock.patch.object(
            SimplePage, "get_vary_headers", autospec=True, return_value=[]
        ) as get_vary_headers:
            self.client.get("/about-us/", headers={"accept": "text/markdown"})
        get_vary_headers.assert_called_once()
        page, request = get_vary_headers.call_args.args
        self.assertEqual(page.url_path, "/home/about-us/")
        self.assertEqual(request.headers["accept"], "text/markdown")

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    def test_vary_added_to_on_serve_page_response(self):
        def on_serve_page(next_serve_page):
            def wrapper(page, request, args, kwargs):
                return HttpResponse("from hook")

            return wrapper

        with hooks.register_temporarily("on_serve_page", on_serve_page):
            response = self.client.get("/about-us/")
        self.assertEqual(response.content, b"from hook")
        self.assertTrue(has_vary_header(response, "Accept"))

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    def test_before_serve_page_response_is_left_alone(self):
        # Responses from before_serve_page hooks are not the page's own response.
        def before_serve_page(page, request, args, kwargs):
            return HttpResponse("from hook")

        with hooks.register_temporarily("before_serve_page", before_serve_page):
            response = self.client.get("/about-us/")
        self.assertEqual(response.content, b"from hook")
        self.assertFalse(has_vary_header(response, "Accept"))

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    @mock.patch.object(SimplePage, "serve", serve_with_markdown)
    def test_private_page(self):
        # View restrictions are checked in an on_serve_page hook, so the
        # password prompt goes through the serve chain and varies too.
        page = SimplePage.objects.get(url_path="/home/about-us/")
        PageViewRestriction.objects.create(
            page=page, restriction_type="password", password="secret"
        )

        prompt = self.client.get("/about-us/", headers={"accept": "text/markdown"})
        self.assertEqual(prompt.status_code, 200)
        self.assertTrue(prompt["Content-Type"].startswith("text/html"))
        self.assertContains(prompt, 'name="password"')
        self.assertTrue(has_vary_header(prompt, "Accept"))
        self.assertIn("no-cache", prompt["Cache-Control"])

        restriction = PageViewRestriction.objects.get(page=page)
        self.client.post(
            reverse(
                "wagtailcore_authenticate_with_password",
                args=[restriction.id, page.id],
            ),
            {"password": "secret", "return_url": "/about-us/"},
        )
        markdown = self.client.get("/about-us/", headers={"accept": "text/markdown"})
        self.assertEqual(markdown["Content-Type"], "text/markdown")
        self.assertTrue(has_vary_header(markdown, "Accept"))

    @mock.patch.object(EventPage, "response_media_types", MARKDOWN_TYPES)
    def test_redirects_and_errors_from_serve_still_vary(self):
        def serve(page, request, *args, **kwargs):
            return HttpResponse(status=410)

        with mock.patch.object(EventPage, "serve", serve):
            response = self.client.get("/events/christmas/")
        self.assertEqual(response.status_code, 410)
        self.assertTrue(has_vary_header(response, "Accept"))

    def test_unknown_page_is_unaffected(self):
        response = self.client.get(
            "/events/quinquagesima/", headers={"accept": "text/markdown"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(has_vary_header(response, "Accept"))


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "wagtail-page-response-variants",
        }
    },
    CACHE_MIDDLEWARE_SECONDS=60,
)
class TestServeVaryHeadersWithCacheMiddleware(PageFixturesMixin, TestCase):
    """
    End-to-end check that a shared cache honouring Vary keeps the variants of
    a page apart. Without the Vary headers, the first response to be cached
    would be served to every client.
    """

    fixtures = ["test.json"]

    def setUp(self):
        Site.clear_site_root_paths_cache()
        from django.core.cache import cache

        cache.clear()
        self.addCleanup(cache.clear)

    def cached_client_get(self, path, **kwargs):
        with self.modify_settings(
            MIDDLEWARE={
                "prepend": "django.middleware.cache.UpdateCacheMiddleware",
                "append": "django.middleware.cache.FetchFromCacheMiddleware",
            }
        ):
            return self.client.get(path, **kwargs)

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    @mock.patch.object(SimplePage, "serve", serve_with_markdown)
    def test_markdown_is_not_served_to_browsers(self):
        markdown = self.cached_client_get(
            "/about-us/", headers={"accept": "text/markdown"}
        )
        self.assertEqual(markdown["Content-Type"], "text/markdown")

        html = self.cached_client_get(
            "/about-us/", headers={"accept": "text/html,*/*;q=0.8"}
        )
        self.assertTrue(html["Content-Type"].startswith("text/html"))
        self.assertContains(html, "<h1>About us</h1>")

        markdown_again = self.cached_client_get(
            "/about-us/", headers={"accept": "text/markdown"}
        )
        self.assertEqual(markdown_again["Content-Type"], "text/markdown")
        self.assertEqual(markdown_again.content, b"# About us")

    @mock.patch.object(SimplePage, "response_media_types", MARKDOWN_TYPES)
    @mock.patch.object(SimplePage, "serve", serve_with_markdown)
    def test_cache_is_active(self):
        # Guards against the tests above passing because nothing was cached.
        self.cached_client_get("/about-us/", headers={"accept": "text/html"})
        with self.assertNumQueries(0):
            response = self.cached_client_get(
                "/about-us/", headers={"accept": "text/html"}
            )
        self.assertContains(response, "<h1>About us</h1>")


class TestRoutablePageVaryHeaders(TestCase):
    def setUp(self):
        home_page = Page.objects.get(id=2)
        self.routable_page = home_page.add_child(
            instance=RoutablePageTest(title="Routable Page", live=True)
        )
        self.url = self.routable_page.url

    @mock.patch.object(RoutablePageTest, "response_media_types", MARKDOWN_TYPES)
    def test_index_route_and_subroutes_vary(self):
        for path in ("", "archive/year/2014/", "render-method-test/"):
            with self.subTest(path=path):
                response = self.client.get(self.url + path)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(has_vary_header(response, "Accept"))

    def test_default_routable_page_does_not_vary(self):
        response = self.client.get(self.url + "archive/year/2014/")
        self.assertFalse(has_vary_header(response, "Accept"))

    @mock.patch.object(RoutablePageTest, "response_media_types", MARKDOWN_TYPES)
    def test_opt_out_for_a_route(self):
        # The pattern documented for routes that always serve one format.
        def get_vary_headers(page, request):
            headers = Page.get_vary_headers(page, request)
            if request.routable_resolver_match.url_name != "index_route":
                headers.remove("Accept")
            return headers

        with mock.patch.object(RoutablePageTest, "get_vary_headers", get_vary_headers):
            index = self.client.get(self.url)
            archive = self.client.get(self.url + "archive/year/2014/")
        self.assertTrue(has_vary_header(index, "Accept"))
        self.assertFalse(has_vary_header(archive, "Accept"))


class TestResponseMediaTypesCheck(SimpleTestCase):
    def get_errors(self, media_types):
        with mock.patch.object(SimplePage, "response_media_types", media_types):
            return [
                error
                for error in SimplePage.check()
                if "response_media_types" in error.msg
            ]

    def test_valid(self):
        for media_types in (
            ["text/html"],
            ["text/html", "text/markdown"],
            ("text/markdown", "text/html"),
        ):
            with self.subTest(media_types=media_types):
                self.assertEqual(self.get_errors(media_types), [])

    def test_invalid(self):
        for media_types in (
            [],
            "text/html",
            ["text/*"],
            ["*/*", "text/html"],
            None,
            ["html"],
            [None],
            [b"text/html"],
        ):
            with self.subTest(media_types=media_types):
                errors = self.get_errors(media_types)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].id, "wagtailcore.E002")
