from django.http import HttpResponse
from django.shortcuts import redirect

from wagtail.contrib.routable_page.models import RoutablePage, path, re_path, route
from wagtail.models import PreviewableMixin


def routable_page_external_view(request, arg="ARG NOT SET"):
    return HttpResponse("EXTERNAL VIEW: " + arg)


class RoutablePageTest(RoutablePage):
    @route(r"^archive/year/1984/$")
    def archive_for_1984(self, request):
        # check that routes are tested in order (and thus this takes precedence over archive_by_year)
        return HttpResponse("we were always at war with eastasia")

    @route(r"^archive/year/(\d+)/$")
    def archive_by_year(self, request, year):
        return HttpResponse("ARCHIVE BY YEAR: " + str(year))

    @route(r"^archive/author/(?P<author_slug>.+)/$")
    def archive_by_author(self, request, author_slug):
        return HttpResponse("ARCHIVE BY AUTHOR: " + author_slug)

    @path("archive/title/<slug:title>/")
    def archive_by_title(self, request, title):
        return HttpResponse("ARCHIVE BY TITLE: " + title)

    @re_path(r"^archive/category/(?P<category_slug>.+)/$")
    def archive_by_category(self, request, category_slug):
        return HttpResponse("ARCHIVE BY CATEGORY: " + category_slug)

    @route(r"^permanant-homepage-redirect/$")
    def permanent_homepage_redirect(self, request):
        return redirect("/", permanent=True)

    @route(r"^temporary-homepage-redirect/$")
    def temporary_homepage_redirect(self, request):
        return redirect("/", permanent=False)

    @route(r"^external/(.+)/$")
    @route(r"^external-no-arg/$")
    def external_view(self, *args, **kwargs):
        return routable_page_external_view(*args, **kwargs)

    # By default, the method name would be used as the url name but when the
    # "name" kwarg is specified, this should override the default.
    @route(r"^override-name-test/$", name="name_overridden")
    def override_name_test(self, request):
        pass

    @route(r"^render-method-test/$")
    def render_method_test(self, request):
        return self.render(request, context_overrides={"self": None, "foo": "bar"})

    @route(r"^render-method-test-custom-template/$")
    def render_method_test_custom_template(self, request):
        return self.render(
            request,
            context_overrides={"self": 1, "foo": "fighters"},
            template="routablepagetests/routable_page_test_alternate.html",
        )

    @route(r"^render-method-with-arg/(?P<slug>.+)/$")
    def render_method_test_with_arg(self, request, slug):
        return self.render(request)

    def get_route_paths(self):
        return [
            "/",
            "/render-method-test/",
            "not-a-valid-route",
        ]

    preview_modes = PreviewableMixin.DEFAULT_PREVIEW_MODES + [
        ("extra", "Extra"),
        ("broken", "Broken"),
    ]

    def serve_preview(self, request, mode_name):
        if mode_name == "broken":
            raise AttributeError("Something is broken!")
        return super().serve_preview(request, mode_name)


class RoutablePageWithOverriddenIndexRouteTest(RoutablePage):
    @route(r"^$")
    def main(self, request):
        return HttpResponse("OVERRIDDEN INDEX ROUTE")
