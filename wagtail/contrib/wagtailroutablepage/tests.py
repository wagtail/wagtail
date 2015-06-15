import unittest
import warnings

import django
from django.test import TestCase, RequestFactory
from django.core.urlresolvers import NoReverseMatch

from wagtail.wagtailcore.models import Page, Site
from wagtail.tests.routablepage.models import OldStyleRoutablePageTest, NewStyleRoutablePageTest, routable_page_external_view
from wagtail.tests.utils import WagtailTestUtils
from wagtail.contrib.wagtailroutablepage.templatetags.wagtailroutablepage_tags import routablepageurl
from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin
from wagtail.utils.deprecation import RemovedInWagtail12Warning


class TestNewStyleRoutablePage(TestCase):
    model = NewStyleRoutablePageTest

    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(instance=self.model(
            title="Routable Page",
            slug='routable-page',
            live=True,
        ))

    def test_resolve_main_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/')

        self.assertEqual(view, self.routable_page.main)
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

    def test_reverse_main_view(self):
        url = self.routable_page.reverse_subpage('main')

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

    def test_get_main_view(self):
        response = self.client.get(self.routable_page.url)

        self.assertContains(response, "MAIN VIEW")

    def test_get_archive_by_year_view(self):
        response = self.client.get(self.routable_page.url + 'archive/year/2014/')

        self.assertContains(response, "ARCHIVE BY YEAR: 2014")

    def test_get_archive_by_author_view(self):
        response = self.client.get(self.routable_page.url + 'archive/author/joe-bloggs/')

        self.assertContains(response, "ARCHIVE BY AUTHOR: joe-bloggs")

    def test_get_external_view(self):
        response = self.client.get(self.routable_page.url + 'external/joe-bloggs/')

        self.assertContains(response, "EXTERNAL VIEW: joe-bloggs")

    def test_get_external_view_other_route(self):
        response = self.client.get(self.routable_page.url + 'external-no-arg/')

        self.assertContains(response, "EXTERNAL VIEW: ARG NOT SET")


@unittest.skipIf(django.VERSION >= (1, 8), "Old style routable pages don't work on Django 1.8")
class TestOldStyleRoutablePage(TestNewStyleRoutablePage, WagtailTestUtils):
    model = OldStyleRoutablePageTest

    def test_resolve_external_view(self):
        view, args, kwargs = self.routable_page.resolve_subpage('/external/joe-bloggs/')

        self.assertEqual(view, routable_page_external_view)
        self.assertEqual(args, ('joe-bloggs', ))
        self.assertEqual(kwargs, {})

    test_resolve_external_view_other_route = None
    test_reverse_external_view_other_route = None
    test_get_external_view_other_route = None

    test_reverse_overridden_name = None
    test_reverse_overridden_name_default_doesnt_work = None

    def test_deprecation_warning(self):
        from django.conf.urls import url

        class TestPageModel(RoutablePageMixin, Page):
            subpage_urls = (
                url('r^$', 'main'),
            )

            def main(self, request):
                pass

            # prevent this class appearing in the global PAGE_MODEL_CLASSES list, as
            # its non-standard location causes failures when translating from content types
            # back to models
            is_abstract = True

            class Meta:
                abstract = True

        # Calling check() should raise a deprecation warning
        # This would usually be called by Django when it loads
        self.reset_warning_registry()
        with warnings.catch_warnings(record=True) as w:
            TestPageModel.check()

            # Check that a RemovedInWagtail12Warning has been triggered
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, RemovedInWagtail12Warning))
            self.assertEqual("wagtailroutablepage.TestPageModel: subpage_urls "
                             "is deprecated. Use the @route decorator to "
                             "define page routes instead.", str(w[-1].message))


class TestRoutablePageTemplateTag(TestCase):
    def setUp(self):
        self.home_page = Page.objects.get(id=2)
        self.routable_page = self.home_page.add_child(instance=NewStyleRoutablePageTest(
            title="Routable Page",
            slug='routable-page',
            live=True,
        ))

        self.rf = RequestFactory()
        self.request = self.rf.get(self.routable_page.url)
        self.request.site = Site.find_for_request(self.request)
        self.context = {'request': self.request}

    def test_templatetag_reverse_main_view(self):
        url = routablepageurl(self.context, self.routable_page,
                              'main')
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
