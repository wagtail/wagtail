from django.http import HttpResponse
from django.conf.urls import url

from wagtail.contrib.wagtailroutablepage.models import RoutablePage


def routable_page_external_view(request, arg):
    return HttpResponse("EXTERNAL VIEW: " + arg)

class RoutablePageTest(RoutablePage):
    @property
    def subpage_urls(self):
        return (
            url(r'^$', self.main, name='main'),
            url(r'^archive/year/(\d+)/$', self.archive_by_year, name='archive_by_year'),
            url(r'^archive/author/(?P<author_slug>.+)/$', self.archive_by_author, name='archive_by_author'),
            url(r'^external/(.+)/$', routable_page_external_view, name='external_view')
        )

    def archive_by_year(self, request, year):
        return HttpResponse("ARCHIVE BY YEAR: " + str(year))

    def archive_by_author(self, request, author_slug):
        return HttpResponse("ARCHIVE BY AUTHOR: " + author_slug)

    def main(self, request):
        return HttpResponse("MAIN VIEW")
