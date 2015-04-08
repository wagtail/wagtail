from django.http import HttpResponse
from django.conf.urls import url

from wagtail.contrib.wagtailroutablepage.models import RoutablePage, route


def routable_page_external_view(request, arg="ARG NOT SET"):
    return HttpResponse("EXTERNAL VIEW: " + arg)


class OldStyleRoutablePageTest(RoutablePage):
    subpage_urls = (
        url(r'^$', 'main', name='main'),
        url(r'^archive/year/(\d+)/$', 'archive_by_year', name='archive_by_year'),
        url(r'^archive/author/(?P<author_slug>.+)/$', 'archive_by_author', name='archive_by_author'),
        url(r'^external/(.+)/$', routable_page_external_view, name='external_view')
    )

    def archive_by_year(self, request, year):
        return HttpResponse("ARCHIVE BY YEAR: " + str(year))

    def archive_by_author(self, request, author_slug):
        return HttpResponse("ARCHIVE BY AUTHOR: " + author_slug)

    def main(self, request):
        return HttpResponse("MAIN VIEW")


class NewStyleRoutablePageTest(RoutablePage):
    @route(r'^$')
    def main(self, request):
        return HttpResponse("MAIN VIEW")

    @route(r'^archive/year/(\d+)/$')
    def archive_by_year(self, request, year):
        return HttpResponse("ARCHIVE BY YEAR: " + str(year))

    @route(r'^archive/author/(?P<author_slug>.+)/$')
    def archive_by_author(self, request, author_slug):
        return HttpResponse("ARCHIVE BY AUTHOR: " + author_slug)

    @route(r'^external/(.+)/$')
    @route(r'^external-no-arg/$')
    def external_view(self, *args, **kwargs):
        return routable_page_external_view(*args, **kwargs)

    # By default, the method name would be used as the url name but when the
    # "name" kwarg is specified, this should override the default.
    @route(r'^override-name-test/$', name='name_overridden')
    def override_name_test(self, request):
        pass
