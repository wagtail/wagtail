from unittest import mock

from django.core import checks
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import path
from django.urls.exceptions import NoReverseMatch

from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import (
    routablepageurl,
)
from wagtail.models import Page, Site
from wagtail.test.routablepage.models import (
    RoutablePageTest,
    RoutablePageWithOverriddenIndexRouteTest,
)


class TestRoutablePage(TestCase):
    model = RoutablePageTest

    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(
            instance=self.model(
                title="Routable Page",
                live=True,
            )
        )

    def test_resolve_index_route_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage("/")

        self.assertEqual(view, self.routable_page.index_route)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_resolve_archive_by_year_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage("/archive/year/2014/")

        self.assertEqual(view, self.routable_page.archive_by_year)
        self.assertEqual(args, ("2014",))
        self.assertEqual(kwargs, {})

    def test_resolve_archive_by_author_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage(
            "/archive/author/joe-bloggs/"
        )

        self.assertEqual(view, self.routable_page.archive_by_author)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"author_slug": "joe-bloggs"})

    def test_resolve_archive_by_title_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage(
            "/archive/title/some-title/"
        )

        self.assertEqual(view, self.routable_page.archive_by_title)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"title": "some-title"})

    def test_resolve_archive_by_category_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage(
            "/archive/category/some-category/"
        )

        self.assertEqual(view, self.routable_page.archive_by_category)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {"category_slug": "some-category"})

    def test_resolve_external_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage("/external/joe-bloggs/")

        self.assertEqual(view, self.routable_page.external_view)
        self.assertEqual(args, ("joe-bloggs",))
        self.assertEqual(kwargs, {})

    def test_resolve_external_view_other_route(self):
        view, args, kwargs = self.routable_page.resolve_subpage("/external-no-arg/")

        self.assertEqual(view, self.routable_page.external_view)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_reverse_index_route_view(self):
        url = self.routable_page.reverse_subpage("index_route")

        self.assertEqual(url, "")

    def test_reverse_archive_by_year_view(self):
        url = self.routable_page.reverse_subpage("archive_by_year", args=("2014",))

        self.assertEqual(url, "archive/year/2014/")

    def test_reverse_archive_by_author_view(self):
        url = self.routable_page.reverse_subpage(
            "archive_by_author", kwargs={"author_slug": "joe-bloggs"}
        )

        self.assertEqual(url, "archive/author/joe-bloggs/")

    def test_reverse_archive_by_title_view(self):
        url = self.routable_page.reverse_subpage(
            "archive_by_title", kwargs={"title": "some-title"}
        )

        self.assertEqual(url, "archive/title/some-title/")

    def test_reverse_overridden_name(self):
        url = self.routable_page.reverse_subpage("name_overridden")

        self.assertEqual(url, "override-name-test/")

    def test_reverse_overridden_name_default_doesnt_work(self):
        with self.assertRaises(NoReverseMatch):
            self.routable_page.reverse_subpage("override_name_test")

    def test_reverse_external_view(self):
        url = self.routable_page.reverse_subpage("external_view", args=("joe-bloggs",))

        self.assertEqual(url, "external/joe-bloggs/")

    def test_reverse_external_view_other_route(self):
        url = self.routable_page.reverse_subpage("external_view")

        self.assertEqual(url, "external-no-arg/")

    def test_get_index_route_view(self):
        with self.assertTemplateUsed("routablepagetests/routable_page_test.html"):
            response = self.client.get(self.routable_page.url)
            context = response.context_data
            self.assertEqual(
                (context["page"], context["self"], context.get("foo")),
                (self.routable_page, self.routable_page, None),
            )
            self.assertEqual(
                context["request"].routable_resolver_match.url_name, "index_route"
            )

    def test_get_render_method_route_view(self):
        with self.assertTemplateUsed("routablepagetests/routable_page_test.html"):
            response = self.client.get(self.routable_page.url + "render-method-test/")
            context = response.context_data
            self.assertEqual(
                (context["page"], context["self"], context["foo"]),
                (self.routable_page, None, "bar"),
            )

    def test_get_render_method_route_view_with_custom_template(self):
        with self.assertTemplateUsed(
            "routablepagetests/routable_page_test_alternate.html"
        ):
            response = self.client.get(
                self.routable_page.url + "render-method-test-custom-template/"
            )
            context = response.context_data
            self.assertEqual(
                (context["page"], context["self"], context["foo"]),
                (self.routable_page, 1, "fighters"),
            )

    def test_get_render_method_route_view_with_arg(self):
        response = self.client.get(
            self.routable_page.url + "render-method-with-arg/foo/"
        )
        resolver_match = response.context_data["request"].routable_resolver_match
        self.assertEqual(resolver_match.url_name, "render_method_test_with_arg")
        self.assertEqual(resolver_match.kwargs, {"slug": "foo"})

    def test_get_routable_page_with_overridden_index_route(self):
        page = self.home_page.add_child(
            instance=RoutablePageWithOverriddenIndexRouteTest(
                title="Routable Page with overridden index", live=True
            )
        )
        response = self.client.get(page.url)
        self.assertContains(response, "OVERRIDDEN INDEX ROUTE")
        self.assertNotContains(response, "DEFAULT PAGE TEMPLATE")

    def test_get_archive_by_year_view(self):
        response = self.client.get(self.routable_page.url + "archive/year/2014/")

        self.assertContains(response, "ARCHIVE BY YEAR: 2014")

    def test_earlier_view_takes_precedence(self):
        response = self.client.get(self.routable_page.url + "archive/year/1984/")

        self.assertContains(response, "we were always at war with eastasia")

    def test_get_archive_by_author_view(self):
        response = self.client.get(
            self.routable_page.url + "archive/author/joe-bloggs/"
        )

        self.assertContains(response, "ARCHIVE BY AUTHOR: joe-bloggs")

    def test_get_archive_by_title_view(self):
        response = self.client.get(self.routable_page.url + "archive/title/some-title/")

        self.assertContains(response, "ARCHIVE BY TITLE: some-title")

    def test_get_archive_by_category_view(self):
        response = self.client.get(
            self.routable_page.url + "archive/category/some-category/"
        )

        self.assertContains(response, "ARCHIVE BY CATEGORY: some-category")

    def test_get_external_view(self):
        response = self.client.get(self.routable_page.url + "external/joe-bloggs/")

        self.assertContains(response, "EXTERNAL VIEW: joe-bloggs")

    def test_get_external_view_other_route(self):
        response = self.client.get(self.routable_page.url + "external-no-arg/")

        self.assertContains(response, "EXTERNAL VIEW: ARG NOT SET")

    def test_routable_page_can_have_instance_bound_descriptors(self):
        # This descriptor pretends that it does not exist in the class, hence
        # it raises an AttributeError when class bound. This is, for instance,
        # the behaviour of django's FileFields.
        class InstanceDescriptor:
            def __get__(self, instance, cls=None):
                if instance is None:
                    raise AttributeError
                return "value"

            def __set__(self, instance, value):
                raise AttributeError

        try:
            RoutablePageTest.descriptor = InstanceDescriptor()
            RoutablePageTest.get_subpage_urls()
        finally:
            del RoutablePageTest.descriptor

    def test_warning_path_with_regex(self):
        route = path(r"^foo/$", lambda request: None, name="path_with_regex")

        warning = checks.Warning(
            "Your URL pattern path_with_regex has a route that contains '(?P<', begins with a '^', or ends with a '$'.",
            hint="Decorate your view with re_path if you want to use regexp.",
            obj=RoutablePageTest,
            id="wagtailroutablepage.W001",
        )
        with mock.patch.object(
            RoutablePageTest, "get_subpage_urls", return_value=[route]
        ):
            self.assertEqual(RoutablePageTest.check(), [warning])


class TestRoutablePageTemplateTag(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(
            instance=RoutablePageTest(
                title="Routable Page",
                live=True,
            )
        )

        self.rf = RequestFactory()
        self.request = self.rf.get(self.routable_page.url)
        self.context = {"request": self.request}

    def test_templatetag_reverse_index_route(self):
        url = routablepageurl(self.context, self.routable_page, "index_route")
        self.assertEqual(url, "/%s/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_year_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_year", "2014"
        )

        self.assertEqual(url, "/%s/archive/year/2014/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_author_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_author",
            author_slug="joe-bloggs",
        )

        self.assertEqual(
            url, "/%s/archive/author/joe-bloggs/" % self.routable_page.slug
        )

    def test_templatetag_reverse_archive_by_title_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_title", title="some-title"
        )

        self.assertEqual(url, "/%s/archive/title/some-title/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_category_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_category",
            category_slug="some-category",
        )

        self.assertEqual(
            url, "/%s/archive/category/some-category/" % self.routable_page.slug
        )

    def test_templatetag_reverse_external_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "external_view", "joe-bloggs"
        )

        self.assertEqual(url, "/%s/external/joe-bloggs/" % self.routable_page.slug)

    def test_templatetag_reverse_external_view_without_append_slash(self):
        with mock.patch("wagtail.models.pages.WAGTAIL_APPEND_SLASH", False):
            url = routablepageurl(
                self.context, self.routable_page, "external_view", "joe-bloggs"
            )
            expected = "/" + self.routable_page.slug + "/" + "external/joe-bloggs/"

        self.assertEqual(url, expected)


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "development.local"])
class TestRoutablePageTemplateTagForSecondSiteAtSameRoot(TestCase):
    """
    When multiple sites exist on the same root page, relative URLs within that subtree should
    omit the domain, in line with #4390
    """

    def setUp(self):
        default_site = Site.objects.get(is_default_site=True)
        second_site = Site.objects.create(  # add another site with the same root page
            hostname="development.local",
            port=default_site.port,
            root_page_id=default_site.root_page_id,
        )

        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(
            instance=RoutablePageTest(
                title="Routable Page",
                live=True,
            )
        )

        self.rf = RequestFactory()
        self.request = self.rf.get(self.routable_page.url)
        self.context = {"request": self.request}
        self.request.META["HTTP_HOST"] = second_site.hostname
        self.request.META["SERVER_PORT"] = second_site.port

    def test_templatetag_reverse_index_route(self):
        url = routablepageurl(self.context, self.routable_page, "index_route")
        self.assertEqual(url, "/%s/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_year_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_year", "2014"
        )

        self.assertEqual(url, "/%s/archive/year/2014/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_author_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_author",
            author_slug="joe-bloggs",
        )

        self.assertEqual(
            url, "/%s/archive/author/joe-bloggs/" % self.routable_page.slug
        )

    def test_templatetag_reverse_archive_by_title_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_title", title="some-title"
        )

        self.assertEqual(url, "/%s/archive/title/some-title/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_category_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_category",
            category_slug="some-category",
        )

        self.assertEqual(
            url, "/%s/archive/category/some-category/" % self.routable_page.slug
        )

    def test_templatetag_reverse_external_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "external_view", "joe-bloggs"
        )

        self.assertEqual(url, "/%s/external/joe-bloggs/" % self.routable_page.slug)

    def test_templatetag_reverse_external_view_without_append_slash(self):
        with mock.patch("wagtail.models.pages.WAGTAIL_APPEND_SLASH", False):
            url = routablepageurl(
                self.context, self.routable_page, "external_view", "joe-bloggs"
            )
            expected = "/" + self.routable_page.slug + "/" + "external/joe-bloggs/"

        self.assertEqual(url, expected)


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "events.local"])
class TestRoutablePageTemplateTagForSecondSiteAtDifferentRoot(TestCase):
    """
    When multiple sites exist, relative URLs between such sites should include the domain portion
    """

    def setUp(self):
        self.home_page = Page.objects.get(id=2)

        events_page = self.home_page.add_child(instance=Page(title="Events", live=True))

        second_site = Site.objects.create(
            hostname="events.local",
            port=80,
            root_page=events_page,
        )

        self.routable_page = self.home_page.add_child(
            instance=RoutablePageTest(
                title="Routable Page",
                live=True,
            )
        )

        self.rf = RequestFactory()
        self.request = self.rf.get(self.routable_page.url)
        self.context = {"request": self.request}

        self.request.META["HTTP_HOST"] = second_site.hostname
        self.request.META["SERVER_PORT"] = second_site.port

    def test_templatetag_reverse_index_route(self):
        url = routablepageurl(self.context, self.routable_page, "index_route")
        self.assertEqual(url, "http://localhost/%s/" % self.routable_page.slug)

    def test_templatetag_reverse_archive_by_year_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_year", "2014"
        )

        self.assertEqual(
            url, "http://localhost/%s/archive/year/2014/" % self.routable_page.slug
        )

    def test_templatetag_reverse_archive_by_author_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_author",
            author_slug="joe-bloggs",
        )

        self.assertEqual(
            url,
            "http://localhost/%s/archive/author/joe-bloggs/" % self.routable_page.slug,
        )

    def test_templatetag_reverse_archive_by_title_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "archive_by_title", title="some-title"
        )

        self.assertEqual(
            url,
            "http://localhost/%s/archive/title/some-title/" % self.routable_page.slug,
        )

    def test_templatetag_reverse_archive_by_category_view(self):
        url = routablepageurl(
            self.context,
            self.routable_page,
            "archive_by_category",
            category_slug="some-category",
        )

        self.assertEqual(
            url,
            "http://localhost/%s/archive/category/some-category/"
            % self.routable_page.slug,
        )

    def test_templatetag_reverse_external_view(self):
        url = routablepageurl(
            self.context, self.routable_page, "external_view", "joe-bloggs"
        )

        self.assertEqual(
            url, "http://localhost/%s/external/joe-bloggs/" % self.routable_page.slug
        )

    def test_templatetag_reverse_external_view_without_append_slash(self):
        with mock.patch("wagtail.models.pages.WAGTAIL_APPEND_SLASH", False):
            url = routablepageurl(
                self.context, self.routable_page, "external_view", "joe-bloggs"
            )
            expected = (
                "http://localhost/"
                + self.routable_page.slug
                + "/"
                + "external/joe-bloggs/"
            )

        self.assertEqual(url, expected)
