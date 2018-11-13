from unittest import mock

from django.test import RequestFactory, TestCase
from django.urls.exceptions import NoReverseMatch

from wagtail.contrib.routable_page.templatetags.wagtailroutablepage_tags import routablepageurl
from wagtail.core.models import Page, Site
from wagtail.tests.routablepage.models import (
    RoutablePageTest, RoutablePageWithOverriddenIndexRouteTest)


class TestRoutablePage(TestCase):
    model = RoutablePageTest

    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(instance=self.model(
            title="Routable Page",
            live=True,
        ))

    def test_resolve_index_route_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/')

        self.assertEqual(view, self.routable_page.index_route)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_resolve_archive_by_year_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/archive/year/2014/')

        self.assertEqual(view, self.routable_page.archive_by_year)
        self.assertEqual(args, ('2014', ))
        self.assertEqual(kwargs, {})

    def test_resolve_archive_by_author_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/archive/author/joe-bloggs/')

        self.assertEqual(view, self.routable_page.archive_by_author)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {'author_slug': 'joe-bloggs'})

    def test_resolve_external_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/external/joe-bloggs/')

        self.assertEqual(view, self.routable_page.external_view)
        self.assertEqual(args, ('joe-bloggs', ))
        self.assertEqual(kwargs, {})

    def test_resolve_external_view_other_route(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/external-no-arg/')

        self.assertEqual(view, self.routable_page.external_view)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_reverse_index_route_view(self):
        url = self.routable_page.reverse_subpage('index_route')

        self.assertEqual(url, '')

    def test_reverse_archive_by_year_view(self):
        url = self.routable_page.reverse_subpage('archive_by_year', args=('2014', ))

        self.assertEqual(url, 'archive/year/2014/')

    def test_reverse_archive_by_author_view(self):
        url = self.routable_page.reverse_subpage('archive_by_author', kwargs={'author_slug': 'joe-bloggs'})

        self.assertEqual(url, 'archive/author/joe-bloggs/')

    def test_reverse_overridden_name(self):
        url = self.routable_page.reverse_subpage('name_overridden')

        self.assertEqual(url, 'override-name-test/')

    def test_reverse_overridden_name_default_doesnt_work(self):
        with self.assertRaises(NoReverseMatch):
            self.routable_page.reverse_subpage('override_name_test')

    def test_reverse_external_view(self):
        url = self.routable_page.reverse_subpage('external_view', args=('joe-bloggs', ))

        self.assertEqual(url, 'external/joe-bloggs/')

    def test_reverse_external_view_other_route(self):
        url = self.routable_page.reverse_subpage('external_view')

        self.assertEqual(url, 'external-no-arg/')

    def test_get_index_route_view(self):
        response = self.client.get(self.routable_page.url)

        self.assertContains(response, "DEFAULT PAGE TEMPLATE")

    def test_get_routable_page_with_overridden_index_route(self):
        page = self.home_page.add_child(
            instance=RoutablePageWithOverriddenIndexRouteTest(
                title="Routable Page with overridden index",
                live=True
            )
        )
        response = self.client.get(page.url)
        self.assertContains(response, "OVERRIDDEN INDEX ROUTE")
        self.assertNotContains(response, "DEFAULT PAGE TEMPLATE")

    def test_get_archive_by_year_view(self):
        response = self.client.get(self.routable_page.url + 'archive/year/2014/')

        self.assertContains(response, "ARCHIVE BY YEAR: 2014")

    def test_earlier_view_takes_precedence(self):
        response = self.client.get(self.routable_page.url + 'archive/year/1984/')

        self.assertContains(response, "we were always at war with eastasia")

    def test_get_archive_by_author_view(self):
        response = self.client.get(self.routable_page.url + 'archive/author/joe-bloggs/')

        self.assertContains(response, "ARCHIVE BY AUTHOR: joe-bloggs")

    def test_get_external_view(self):
        response = self.client.get(self.routable_page.url + 'external/joe-bloggs/')

        self.assertContains(response, "EXTERNAL VIEW: joe-bloggs")

    def test_get_external_view_other_route(self):
        response = self.client.get(self.routable_page.url + 'external-no-arg/')

        self.assertContains(response, "EXTERNAL VIEW: ARG NOT SET")

    def test_routable_page_can_have_instance_bound_descriptors(self):
        # This descriptor pretends that it does not exist in the class, hence
        # it raises an AttributeError when class bound. This is, for instance,
        # the behavior of django's FileFields.
        class InstanceDescriptor:
            def __get__(self, instance, cls=None):
                if instance is None:
                    raise AttributeError
                return 'value'

            def __set__(self, instance, value):
                raise AttributeError

        try:
            RoutablePageTest.descriptor = InstanceDescriptor()
            RoutablePageTest.get_subpage_urls()
        finally:
            del RoutablePageTest.descriptor


class TestRoutablePageTemplateTag(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(instance=RoutablePageTest(
            title="Routable Page",
            live=True,
        ))

        self.rf = RequestFactory()
        self.request = self.rf.get(self.routable_page.url)
        self.request.site = Site.find_for_request(self.request)
        self.context = {'request': self.request}

    def test_templatetag_reverse_index_route(self):
        url = routablepageurl(self.context, self.routable_page,
                              'index_route')
        self.assertEqual(url, self.routable_page.url)

    def test_templatetag_reverse_archive_by_year_view(self):
        url = routablepageurl(self.context, self.routable_page,
                              'archive_by_year', '2014')

        self.assertEqual(url, self.routable_page.url + 'archive/year/2014/')

    def test_templatetag_reverse_archive_by_author_view(self):
        url = routablepageurl(self.context, self.routable_page,
                              'archive_by_author', author_slug='joe-bloggs')

        self.assertEqual(url, self.routable_page.url + 'archive/author/joe-bloggs/')

    def test_templatetag_reverse_external_view(self):
        url = routablepageurl(self.context, self.routable_page,
                              'external_view', 'joe-bloggs')

        self.assertEqual(url, self.routable_page.url + 'external/joe-bloggs/')

    def test_templatetag_reverse_external_view_without_append_slash(self):
        with mock.patch('wagtail.core.models.WAGTAIL_APPEND_SLASH', False):
            url = routablepageurl(self.context, self.routable_page,
                                  'external_view', 'joe-bloggs')
            expected = self.routable_page.url + '/' + 'external/joe-bloggs/'

        self.assertEqual(url, expected)
