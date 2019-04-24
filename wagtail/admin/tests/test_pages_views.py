import datetime
import logging
import os
from itertools import chain
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import constants as message_constants
from django.core import mail, paginator
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_delete, pre_delete
from django.http import HttpRequest, HttpResponse
from django.test import TestCase, modify_settings, override_settings
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.dateparse import parse_date
from freezegun import freeze_time

from wagtail.admin.views.home import RecentEditsPanel
from wagtail.admin.views.pages import PreviewOnEdit
from wagtail.core.models import GroupPagePermission, Page, PageRevision, Site
from wagtail.core.signals import page_published, page_unpublished
from wagtail.search.index import SearchField
from wagtail.tests.testapp.models import (
    EVENT_AUDIENCE_CHOICES, Advert, AdvertPlacement, BusinessChild, BusinessIndex, BusinessSubIndex,
    DefaultStreamPage, EventCategory, EventPage, EventPageCarouselItem, FilePage,
    FormClassAdditionalFieldPage, ManyToManyBlogPage, SimplePage, SingleEventPage, SingletonPage,
    SingletonPageViaMaxCount, StandardChild, StandardIndex, TaggedPage)
from wagtail.tests.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


def submittable_timestamp(timestamp):
    """
    Helper function to translate a possibly-timezone-aware datetime into the format used in the
    go_live_at / expire_at form fields - "YYYY-MM-DD hh:mm", with no timezone indicator.
    This will be interpreted as being in the server's timezone (settings.TIME_ZONE), so we
    need to pass it through timezone.localtime to ensure that the client and server are in
    agreement about what the timestamp means.
    """
    return timezone.localtime(timestamp).strftime("%Y-%m-%d %H:%M")


def local_datetime(*args):
    dt = datetime.datetime(*args)
    return timezone.make_aware(dt)


class TestPageExplorer(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)

        # more child pages to test ordering
        self.old_page = StandardIndex(
            title="Old page",
            slug="old-page",
            latest_revision_created_at=local_datetime(2010, 1, 1)
        )
        self.root_page.add_child(instance=self.old_page)

        self.new_page = SimplePage(
            title="New page",
            slug="new-page",
            content="hello",
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        self.root_page.add_child(instance=self.new_page)

        # Login
        self.user = self.login()

    def test_explore(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(self.root_page, response.context['parent_page'])

        # child pages should be most recent first
        # (with null latest_revision_created_at at the end)
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.new_page.id, self.old_page.id, self.child_page.id])

    def test_explore_root(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(Page.objects.get(id=1), response.context['parent_page'])
        self.assertTrue(response.context['pages'].paginator.object_list.filter(id=self.root_page.id).exists())

    def test_explore_root_shows_icon(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)

        # Administrator (or user with add_site permission) should see the
        # sites link with the icon-site icon
        self.assertContains(
            response,
            ("""<a href="/admin/sites/" class="icon icon-site" """
             """title="Sites menu"></a>""")
        )

    def test_ordering(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'ordering': 'title'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], 'title')

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.child_page.id, self.new_page.id, self.old_page.id])

    def test_reverse_ordering(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'ordering': '-title'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], '-title')

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.old_page.id, self.new_page.id, self.child_page.id])

    def test_ordering_by_last_revision_forward(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'ordering': 'latest_revision_created_at'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], 'latest_revision_created_at')

        # child pages should be oldest revision first
        # (with null latest_revision_created_at at the start)
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.child_page.id, self.old_page.id, self.new_page.id])

    def test_invalid_ordering(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'ordering': 'invalid_order'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], '-latest_revision_created_at')

    def test_reordering(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'ordering': 'ord'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], 'ord')

        # child pages should be ordered by native tree order (i.e. by creation time)
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.child_page.id, self.old_page.id, self.new_page.id])

        # Pages must not be paginated
        self.assertNotIsInstance(response.context['pages'], paginator.Page)

    def test_construct_explorer_page_queryset_hook(self):
        # testapp implements a construct_explorer_page_queryset hook
        # that only returns pages with a slug starting with 'hello'
        # when the 'polite_pages_only' URL parameter is set
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
            {'polite_pages_only': 'yes_please'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [self.child_page.id])

    def make_pages(self):
        for i in range(150):
            self.root_page.add_child(instance=SimplePage(
                title="Page " + str(i),
                slug="page-" + str(i),
                content="hello",
            ))

    def test_pagination(self):
        self.make_pages()

        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )), {'p': 2})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')

        # Check that we got the correct page
        self.assertEqual(response.context['pages'].number, 2)

    def test_pagination_invalid(self):
        self.make_pages()

        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )), {'p': 'Hello World!'})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')

        # Check that we got page one
        self.assertEqual(response.context['pages'].number, 1)

    def test_pagination_out_of_range(self):
        self.make_pages()

        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )), {'p': 99999})

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')

        # Check that we got the last page
        self.assertEqual(response.context['pages'].number, response.context['pages'].paginator.num_pages)

    def test_listing_uses_specific_models(self):
        # SingleEventPage has custom URL routing; the 'live' link in the listing
        # should show the custom URL, which requires us to use the specific version
        # of the class
        self.new_event = SingleEventPage(
            title="New event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        self.root_page.add_child(instance=self.new_event)

        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '/new-event/pointless-suffix/')

    def make_event_pages(self, count):
        for i in range(count):
            self.root_page.add_child(instance=SingleEventPage(
                title="New event " + str(i),
                location='the moon', audience='public',
                cost='free', date_from='2001-01-01',
                latest_revision_created_at=local_datetime(2016, 1, 1)
            ))

    def test_exploring_uses_specific_page_with_custom_display_title(self):
        # SingleEventPage has a custom get_admin_display_title method; explorer should
        # show the custom title rather than the basic database one
        self.make_event_pages(count=1)
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertContains(response, 'New event 0 (single event)')

        new_event = SingleEventPage.objects.latest('pk')
        response = self.client.get(reverse('wagtailadmin_explore', args=(new_event.id, )))
        self.assertContains(response, 'New event 0 (single event)')

    def test_ordering_less_than_100_pages_uses_specific_page_with_custom_display_title(self):
        # Reorder view should also use specific pages
        # (provided there are <100 pages in the listing, as this may be a significant
        # performance hit on larger listings)
        # There are 3 pages created in setUp, so 96 more add to a total of 99.
        self.make_event_pages(count=96)
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )) + '?ordering=ord')
        self.assertContains(response, 'New event 0 (single event)')

    def test_ordering_100_or_more_pages_uses_generic_page_without_custom_display_title(self):
        # There are 3 pages created in setUp, so 97 more add to a total of 100.
        self.make_event_pages(count=97)
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )) + '?ordering=ord')
        self.assertNotContains(response, 'New event 0 (single event)')

    def test_parent_page_is_specific(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context['parent_page'], SimplePage)

    def test_explorer_no_perms(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        admin = reverse('wagtailadmin_home')
        self.assertRedirects(
            self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, ))),
            admin)
        self.assertRedirects(
            self.client.get(reverse('wagtailadmin_explore_root')), admin)

    def test_explore_with_missing_page_model(self):
        # Create a ContentType that doesn't correspond to a real model
        missing_page_content_type = ContentType.objects.create(app_label='tests', model='missingpage')
        # Turn /home/old-page/ into this content type
        Page.objects.filter(id=self.old_page.id).update(content_type=missing_page_content_type)

        # try to browse the the listing that contains the missing model
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')

        # try to browse into the page itself
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.old_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')


class TestBreadcrumb(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def test_breadcrumb_uses_specific_titles(self):
        self.user = self.login()

        # get the explorer view for a subpage of a SimplePage
        page = Page.objects.get(url_path='/home/secret-plans/steal-underpants/')
        response = self.client.get(reverse('wagtailadmin_explore', args=(page.id, )))

        # The breadcrumb should pick up SimplePage's overridden get_admin_display_title method
        expected_url = reverse('wagtailadmin_explore', args=(Page.objects.get(url_path='/home/secret-plans/').id, ))
        self.assertContains(response, """<li><a href="%s">Secret plans (simple page)</a></li>""" % expected_url)


class TestPageExplorerSignposting(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=1)

        # Find page with an associated site
        self.site_page = Page.objects.get(id=2)

        # Add another top-level page (which will have no corresponding site record)
        self.no_site_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.no_site_page)

    # Tests for users that have both add-site permission, and explore permission at the given view;
    # warning messages should include advice re configuring sites

    def test_admin_at_root(self):
        self.assertTrue(self.client.login(username='superuser', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)
        # Administrator (or user with add_site permission) should get the full message
        # about configuring sites
        self.assertContains(
            response,
            (
                "The root level is where you can add new sites to your Wagtail installation. "
                "Pages created here will not be accessible at any URL until they are associated with a site."
            )
        )
        self.assertContains(response, """<a href="/admin/sites/">Configure a site now.</a>""")

    def test_admin_at_non_site_page(self):
        self.assertTrue(self.client.login(username='superuser', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.no_site_page.id, )))
        self.assertEqual(response.status_code, 200)
        # Administrator (or user with add_site permission) should get a warning about
        # unroutable pages, and be directed to the site config area
        self.assertContains(
            response,
            (
                "There is no site set up for this location. "
                "Pages created here will not be accessible at any URL until a site is associated with this location."
            )
        )
        self.assertContains(response, """<a href="/admin/sites/">Configure a site now.</a>""")

    def test_admin_at_site_page(self):
        self.assertTrue(self.client.login(username='superuser', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.site_page.id, )))
        self.assertEqual(response.status_code, 200)
        # There should be no warning message here
        self.assertNotContains(response, "Pages created here will not be accessible")

    # Tests for standard users that have explore permission at the given view;
    # warning messages should omit advice re configuring sites

    def test_nonadmin_at_root(self):
        # Assign siteeditor permission over no_site_page, so that the deepest-common-ancestor
        # logic allows them to explore root
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.no_site_page, permission_type='add'
        )
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore_root'))

        self.assertEqual(response.status_code, 200)
        # Non-admin should get a simple "create pages as children of the homepage" prompt
        self.assertContains(
            response,
            "Pages created here will not be accessible at any URL. "
            "To add pages to an existing site, create them as children of the homepage."
        )

    def test_nonadmin_at_non_site_page(self):
        # Assign siteeditor permission over no_site_page
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.no_site_page, permission_type='add'
        )
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.no_site_page.id, )))

        self.assertEqual(response.status_code, 200)
        # Non-admin should get a warning about unroutable pages
        self.assertContains(
            response,
            (
                "There is no site record for this location. "
                "Pages created here will not be accessible at any URL."
            )
        )

    def test_nonadmin_at_site_page(self):
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.site_page.id, )))
        self.assertEqual(response.status_code, 200)
        # There should be no warning message here
        self.assertNotContains(response, "Pages created here will not be accessible")

    # Tests for users that have explore permission *somewhere*, but not at the view being tested;
    # in all cases, they should be redirected to their explorable root

    def test_bad_permissions_at_root(self):
        # 'siteeditor' does not have permission to explore the root
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore_root'))

        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response['Location']),
            (302, reverse('wagtailadmin_explore', args=(self.site_page.pk, )))
        )

    def test_bad_permissions_at_non_site_page(self):
        # 'siteeditor' does not have permission to explore no_site_page
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.no_site_page.id, )))

        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response['Location']),
            (302, reverse('wagtailadmin_explore', args=(self.site_page.pk, )))
        )

    def test_bad_permissions_at_site_page(self):
        # Adjust siteeditor's permission so that they have permission over no_site_page
        # instead of site_page
        Group.objects.get(name="Site-wide editors").page_permissions.update(page_id=self.no_site_page.id)
        self.assertTrue(self.client.login(username='siteeditor', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.site_page.id, )))
        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response['Location']),
            (302, reverse('wagtailadmin_explore', args=(self.no_site_page.pk, )))
        )


class TestExplorablePageVisibility(TestCase, WagtailTestUtils):
    """
    Test the way that the Explorable Pages functionality manifests within the Explorer.
    This is isolated in its own test case because it requires a custom page tree and custom set of
    users and groups.
    The fixture sets up this page tree:
    ========================================================
    ID Site          Path
    ========================================================
    1              /
    2  testserver  /home/
    3  testserver  /home/about-us/
    4  example.com /example-home/
    5  example.com /example-home/content/
    6  example.com /example-home/content/page-1/
    7  example.com /example-home/content/page-2/
    9  example.com /example-home/content/page-2/child-1
    8  example.com /example-home/other-content/
    10 example2.com /home-2/
    ========================================================
    Group 1 has explore and choose permissions rooted at testserver's homepage.
    Group 2 has explore and choose permissions rooted at example.com's page-1.
    Group 3 has explore and choose permissions rooted at example.com's other-content.
    User "jane" is in Group 1.
    User "bob" is in Group 2.
    User "sam" is in Groups 1 and 2.
    User "josh" is in Groups 2 and 3.
    User "mary" is is no Groups, but she has the "access wagtail admin" permission.
    User "superman" is an admin.
    """

    fixtures = ['test_explorable_pages.json']

    # Integration tests adapted from @coredumperror

    def test_admin_can_explore_every_page(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        for page in Page.objects.all():
            response = self.client.get(reverse('wagtailadmin_explore', args=[page.pk]))
            self.assertEqual(response.status_code, 200)

    def test_admin_sees_root_page_as_explorer_root(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)
        # Administrator should see the full list of children of the Root page.
        self.assertContains(response, "Welcome to testserver!")
        self.assertContains(response, "Welcome to example.com!")

    def test_admin_sees_breadcrumbs_up_to_root_page(self):
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=[6]))
        self.assertEqual(response.status_code, 200)

        self.assertInHTML(
            """<li class="home"><a href="/admin/pages/" class="icon icon-site text-replace">Root</a></li>""",
            str(response.content)
        )
        self.assertInHTML("""<li><a href="/admin/pages/4/">Welcome to example.com!</a></li>""", str(response.content))
        self.assertInHTML("""<li><a href="/admin/pages/5/">Content</a></li>""", str(response.content))

    def test_nonadmin_sees_breadcrumbs_up_to_cca(self):
        self.assertTrue(self.client.login(username='josh', password='password'))
        response = self.client.get(reverse('wagtailadmin_explore', args=[6]))
        self.assertEqual(response.status_code, 200)
        # While at "Page 1", Josh should see the breadcrumbs leading only as far back as the example.com homepage,
        # since it's his Closest Common Ancestor.
        self.assertInHTML(
            """<li class="home"><a href="/admin/pages/4/" class="icon icon-home text-replace">Home</a></li>""",
            str(response.content)
        )
        self.assertInHTML("""<li><a href="/admin/pages/5/">Content</a></li>""", str(response.content))
        # The page title shouldn't appear because it's the "home" breadcrumb.
        self.assertNotContains(response, "Welcome to example.com!")

    def test_admin_home_page_changes_with_permissions(self):
        self.assertTrue(self.client.login(username='bob', password='password'))
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # Bob should only see the welcome for example.com, not testserver
        self.assertContains(response, "Welcome to the example.com Wagtail CMS")
        self.assertNotContains(response, "testserver")

    def test_breadcrumb_with_no_user_permissions(self):
        self.assertTrue(self.client.login(username='mary', password='password'))
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # Since Mary has no page permissions, she should not see the breadcrumb
        self.assertNotContains(response, """<li class="home"><a href="/admin/pages/4/" class="icon icon-home text-replace">Home</a></li>""")


class TestPageCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_add_subpage(self):
        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Simple page")
        target_url = reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id))
        self.assertContains(response, 'href="%s"' % target_url)
        # List of available page types should not contain pages with is_creatable = False
        self.assertNotContains(response, "MTI base page")
        # List of available page types should not contain abstract pages
        self.assertNotContains(response, "Abstract page")
        # List of available page types should not contain pages whose parent_page_types forbid it
        self.assertNotContains(response, "Business child")

    def test_add_subpage_with_subpage_types(self):
        # Add a BusinessIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)

        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(business_index.id, )))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Business child")
        # List should not contain page types not in the subpage_types list
        self.assertNotContains(response, "Simple page")

    def test_add_subpage_with_one_valid_subpage_type(self):
        # Add a BusinessSubIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)
        business_subindex = BusinessSubIndex(
            title="Hello world!",
            slug="hello-world",
        )
        business_index.add_child(instance=business_subindex)

        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(business_subindex.id, )))
        # Should be redirected to the 'add' page for BusinessChild, the only valid subpage type
        self.assertRedirects(
            response,
            reverse('wagtailadmin_pages:add', args=('tests', 'businesschild', business_subindex.id))
        )

    def test_add_subpage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get add subpage page
        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(self.root_page.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_add_subpage_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(100000, )))
        self.assertEqual(response.status_code, 404)

    def test_add_subpage_with_next_param(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:add_subpage', args=(self.root_page.id, )),
            {'next': '/admin/users/'}
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Simple page")
        target_url = reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id))
        self.assertContains(response, 'href="%s?next=/admin/users/"' % target_url)

    def test_create_simplepage(self):
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="#tab-content" class="active">Content</a>')
        self.assertContains(response, '<a href="#tab-promote" class="">Promote</a>')
        # test register_page_action_menu_item hook
        self.assertContains(response, '<input type="submit" name="action-panic" value="Panic!" class="button" />')
        self.assertContains(response, 'testapp/js/siren.js')
        # test construct_page_action_menu hook
        self.assertContains(response, '<input type="submit" name="action-relax" value="Relax." class="button" />')

    def test_create_multipart(self):
        """
        Test checks if 'enctype="multipart/form-data"' is added and only to forms that require multipart encoding.
        """
        # check for SimplePage where is no file field
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'enctype="multipart/form-data"')
        self.assertTemplateUsed(response, 'wagtailadmin/pages/create.html')

        # check for FilePage which has file field
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'filepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_create_page_without_promote_tab(self):
        """
        Test that the Promote tab is not rendered for page classes that define it as empty
        """
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="#tab-content" class="active">Content</a>')
        self.assertNotContains(response, '<a href="#tab-promote" class="">Promote</a>')

    def test_create_page_with_custom_tabs(self):
        """
        Test that custom edit handlers are rendered
        """
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardchild', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="#tab-content" class="active">Content</a>')
        self.assertContains(response, '<a href="#tab-promote" class="">Promote</a>')
        self.assertContains(response, '<a href="#tab-dinosaurs" class="">Dinosaurs</a>')

    def test_create_page_with_non_model_field(self):
        """
        Test that additional fields defined on the form rather than the model are accepted and rendered
        """
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'formclassadditionalfieldpage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/create.html')
        self.assertContains(response, "Enter SMS authentication code")

    def test_create_simplepage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get page
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_cannot_create_page_with_is_creatable_false(self):
        # tests.MTIBasePage has is_creatable=False, so attempting to add a new one
        # should fail with permission denied
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'mtibasepage', self.root_page.id))
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_create_page_when_can_create_at_returns_false(self):
        # issue #2892

        # Check that creating a second SingletonPage results in a permission
        # denied error.

        # SingletonPage overrides the can_create_at method to make it return
        # False if another SingletonPage already exists.

        # The Page model now has a max_count attribute (issue 4841),
        # but we are leaving this test in place to cover existing behaviour and
        # ensure it does not break any code doing this in the wild.
        add_url = reverse('wagtailadmin_pages:add', args=[
            SingletonPage._meta.app_label, SingletonPage._meta.model_name, self.root_page.pk])

        # A single singleton page should be creatable
        self.assertTrue(SingletonPage.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

        # Create a singleton page
        self.root_page.add_child(instance=SingletonPage(
            title='singleton', slug='singleton'))

        # A second singleton page should not be creatable
        self.assertFalse(SingletonPage.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 403)

    def test_cannot_create_singleton_page_with_max_count(self):
        # Check that creating a second SingletonPageViaMaxCount results in a permission
        # denied error.

        # SingletonPageViaMaxCount uses the max_count attribute to limit the number of
        # instance it can have.

        add_url = reverse('wagtailadmin_pages:add', args=[
            SingletonPageViaMaxCount._meta.app_label, SingletonPageViaMaxCount._meta.model_name, self.root_page.pk])

        # A single singleton page should be creatable
        self.assertTrue(SingletonPageViaMaxCount.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)

        # Create a singleton page
        self.root_page.add_child(instance=SingletonPageViaMaxCount(
            title='singleton', slug='singleton'))

        # A second singleton page should not be creatable
        self.assertFalse(SingletonPageViaMaxCount.can_create_at(self.root_page))
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 403)

    def test_cannot_create_page_with_wrong_parent_page_types(self):
        # tests.BusinessChild has limited parent_page_types, so attempting to add
        # a new one at the root level should fail with permission denied
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'businesschild', self.root_page.id))
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_create_page_with_wrong_subpage_types(self):
        # Add a BusinessIndex to test business rules in
        business_index = BusinessIndex(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=business_index)

        # BusinessIndex has limited subpage_types, so attempting to add a SimplePage
        # underneath it should fail with permission denied
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', business_index.id))
        )
        self.assertEqual(response.status_code, 403)

    def test_create_simplepage_post(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)),
            post_data
        )

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(page.id, )))

        self.assertEqual(page.title, post_data['title'])
        self.assertEqual(page.draft_title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_create_simplepage_scheduled(self):
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check the scheduled times
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEqual(page.go_live_at.date(), go_live_at.date())
        self.assertEqual(page.expire_at.date(), expire_at.date())
        self.assertEqual(page.expired, False)
        self.assertTrue(page.status_string, "draft")

        # No revisions with approved_go_live_at
        self.assertFalse(PageRevision.objects.filter(page=page).exclude(approved_go_live_at__isnull=True).exists())

    def test_create_simplepage_scheduled_go_live_before_expiry(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=2)),
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=1)),
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'go_live_at', "Go live date/time must be before expiry date/time")
        self.assertFormError(response, 'form', 'expire_at', "Go live date/time must be before expiry date/time")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_simplepage_scheduled_expire_in_the_past(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=-1)),
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'expire_at', "Expiry date/time must be in the future")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_simplepage_post_publish(self):
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Post
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        self.assertEqual(page.title, post_data['title'])
        self.assertEqual(page.draft_title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertTrue(page.live)
        self.assertTrue(page.first_published_at)

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], page.specific_class)
        self.assertEqual(mock_call['instance'], page)
        self.assertIsInstance(mock_call['instance'], page.specific_class)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_create_simplepage_post_publish_scheduled(self):
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEqual(page.go_live_at.date(), go_live_at.date())
        self.assertEqual(page.expire_at.date(), expire_at.date())
        self.assertEqual(page.expired, False)

        # A revision with approved_go_live_at should exist now
        self.assertTrue(PageRevision.objects.filter(page=page).exclude(approved_go_live_at__isnull=True).exists())
        # But Page won't be live
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)
        self.assertTrue(page.status_string, "scheduled")

    def test_create_simplepage_post_submit(self):
        # Create a moderator user for testing email
        get_user_model().objects.create_superuser('moderator', 'moderator@email.com', 'password')

        # Submit
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)
        self.assertFalse(page.first_published_at)

        # The latest revision for the page should now be in moderation
        self.assertTrue(page.get_latest_revision().submitted_for_moderation)

        # Check that the moderator got an email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['moderator@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "New page!" has been submitted for moderation')

    def test_create_simplepage_post_existing_slug(self):
        # This tests the existing slug checking on page save

        # Create a page
        self.child_page = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Attempt to create a new one with the same slug
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'slug', "This slug is already in use")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_create_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', 100000)))
        self.assertEqual(response.status_code, 404)

    def test_create_nonpagetype(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('wagtailimages', 'image', self.root_page.id))
        )
        self.assertEqual(response.status_code, 404)

    def test_preview_on_create(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_add',
                              args=('tests', 'simplepage', self.root_page.id))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "New page!")

        # Check that the treebeard attributes were set correctly on the page object
        self.assertEqual(response.context['self'].depth, self.root_page.depth + 1)
        self.assertTrue(response.context['self'].path.startswith(self.root_page.path))
        self.assertEqual(response.context['self'].get_parent(), self.root_page)

    def test_whitespace_titles(self):
        post_data = {
            'title': " ",  # Single space on purpose
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

    def test_whitespace_titles_with_tab(self):
        post_data = {
            'title': "\t",  # Single space on purpose
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

    def test_whitespace_titles_with_tab_in_seo_title(self):
        post_data = {
            'title': "Hello",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
            'seo_title': '\t'
        }
        response = self.client.post(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be successful, as seo_title is not required
        self.assertEqual(response.status_code, 302)

        # The tab should be automatically stripped from the seo_title
        page = Page.objects.order_by('-id').first()
        self.assertEqual(page.seo_title, '')

    def test_whitespace_is_stripped_from_titles(self):
        post_data = {
            'title': "   Hello   ",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
            'seo_title': '   hello SEO   '
        }
        response = self.client.post(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be successful, as both title and seo_title are non-empty after stripping
        self.assertEqual(response.status_code, 302)

        # Whitespace should be automatically stripped from title and seo_title
        page = Page.objects.order_by('-id').first()
        self.assertEqual(page.title, 'Hello')
        self.assertEqual(page.draft_title, 'Hello')
        self.assertEqual(page.seo_title, 'hello SEO')

    def test_long_slug(self):
        post_data = {
            'title': "Hello world",
            'content': "Some content",
            'slug': 'hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-'
                    'hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-'
                    'hello-world-hello-world-hello-world-hello-world-hello-world-hello-world-'
                    'hello-world-hello-world-hello-world-hello-world-hello-world-hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)), post_data
        )

        # Check that a form error was raised
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'slug', "Ensure this value has at most 255 characters (it has 287).")

    def test_before_create_page_hook(self):
        def hook_func(request, parent_page, page_class):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(parent_page.id, self.root_page.id)
            self.assertEqual(page_class, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_create_page', hook_func):
            response = self.client.get(
                reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id))
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_create_page_hook_post(self):
        def hook_func(request, parent_page, page_class):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(parent_page.id, self.root_page.id)
            self.assertEqual(page_class, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_create_page', hook_func):
            post_data = {
                'title': "New page!",
                'content': "Some content",
                'slug': 'hello-world',
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)),
                post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be created
        self.assertFalse(Page.objects.filter(title="New page!").exists())

    def test_after_create_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('after_create_page', hook_func):
            post_data = {
                'title': "New page!",
                'content': "Some content",
                'slug': 'hello-world',
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)),
                post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be created
        self.assertTrue(Page.objects.filter(title="New page!").exists())


class TestPerRequestEditHandler(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.root_page, permission_type='add'
        )

    def test_create_page_with_per_request_custom_edit_handlers(self):
        """
        Test that per-request custom behaviour in edit handlers is honoured
        """
        # non-superusers should not see secret_data
        logged_in = self.client.login(username='siteeditor', password='password')
        self.assertTrue(logged_in)
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'secretpage', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"boring_data"')
        self.assertNotContains(response, '"secret_data"')

        # superusers should see secret_data
        logged_in = self.client.login(username='superuser', password='password')
        self.assertTrue(logged_in)
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'secretpage', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"boring_data"')
        self.assertContains(response, '"secret_data"')


class TestPageEdit(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SimplePage.objects.get(id=child_page.id)

        # Add file page
        fake_file = ContentFile("File for testing multipart")
        fake_file.name = 'test.txt'
        file_page = FilePage(
            title="File Page",
            slug="file-page",
            file_field=fake_file,
        )
        self.root_page.add_child(instance=file_page)
        file_page.save_revision().publish()
        self.file_page = FilePage.objects.get(id=file_page.id)

        # Add event page (to test edit handlers)
        self.event_page = EventPage(
            title="Event page", slug="event-page",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=self.event_page)

        # Add single event page (to test custom URL routes)
        self.single_event_page = SingleEventPage(
            title="Mars landing", slug="mars-landing",
            location='mars', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.root_page.add_child(instance=self.single_event_page)

        self.unpublished_page = SimplePage(
            title="Hello unpublished world!",
            slug="hello-unpublished-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        self.root_page.add_child(instance=self.unpublished_page)

        # Login
        self.user = self.login()

    def test_page_edit(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Test InlinePanel labels/headings
        self.assertContains(response, '<legend>Speaker lineup</legend>')
        self.assertContains(response, 'Add speakers')

        # test register_page_action_menu_item hook
        self.assertContains(response, '<input type="submit" name="action-panic" value="Panic!" class="button" />')
        self.assertContains(response, 'testapp/js/siren.js')

        # test construct_page_action_menu hook
        self.assertContains(response, '<input type="submit" name="action-relax" value="Relax." class="button" />')

    def test_edit_draft_page_with_no_revisions(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.unpublished_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_edit_multipart(self):
        """
        Test checks if 'enctype="multipart/form-data"' is added and only to forms that require multipart encoding.
        """
        # check for SimplePage where is no file field
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'enctype="multipart/form-data"')
        self.assertTemplateUsed(response, 'wagtailadmin/pages/edit.html')

        # check for FilePage which has file field
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.file_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_upload_file_publish(self):
        """
        Check that file uploads work when directly publishing
        """
        file_upload = ContentFile(b"A new file", name='published-file.txt')
        post_data = {
            'title': 'New file',
            'slug': 'new-file',
            'file_field': file_upload,
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=[self.file_page.id]), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=[self.root_page.id]))

        # Check the new file exists
        file_page = FilePage.objects.get()

        self.assertEqual(file_page.file_field.name, file_upload.name)
        self.assertTrue(os.path.exists(file_page.file_field.path))
        self.assertEqual(file_page.file_field.read(), b"A new file")

    def test_upload_file_draft(self):
        """
        Check that file uploads work when saving a draft
        """
        file_upload = ContentFile(b"A new file", name='draft-file.txt')
        post_data = {
            'title': 'New file',
            'slug': 'new-file',
            'file_field': file_upload,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=[self.file_page.id]), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=[self.file_page.id]))

        # Check the file was uploaded
        file_path = os.path.join(settings.MEDIA_ROOT, file_upload.name)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'rb') as saved_file:
            self.assertEqual(saved_file.read(), b"A new file")

        # Publish the draft just created
        FilePage.objects.get().get_latest_revision().publish()

        # Get the file page, check the file is set
        file_page = FilePage.objects.get()
        self.assertEqual(file_page.file_field.name, file_upload.name)
        self.assertTrue(os.path.exists(file_page.file_field.path))
        self.assertEqual(file_page.file_field.read(), b"A new file")

    def test_page_edit_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get edit page
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_edit_post(self):
        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

        # Page fields should not be changed (because we just created a new draft)
        self.assertEqual(child_page_new.title, self.child_page.title)
        self.assertEqual(child_page_new.content, self.child_page.content)
        self.assertEqual(child_page_new.slug, self.child_page.slug)

        # The draft_title should have a new title
        self.assertEqual(child_page_new.draft_title, post_data['title'])

    def test_page_edit_post_when_locked(self):
        # Tests that trying to edit a locked page results in an error

        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        # Post
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Shouldn't be redirected
        self.assertContains(response, "The page could not be saved as it is locked")

        # The page shouldn't have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertFalse(child_page_new.has_unpublished_changes)

    def test_edit_post_scheduled(self):
        # put go_live_at and expire_at several days away from the current date, to avoid
        # false matches in content_json__contains tests
        go_live_at = timezone.now() + datetime.timedelta(days=10)
        expire_at = timezone.now() + datetime.timedelta(days=20)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page will still be live
        self.assertTrue(child_page_new.live)

        # A revision with approved_go_live_at should not exist
        self.assertFalse(PageRevision.objects.filter(
            page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # But a revision with go_live_at and expire_at in their content json *should* exist
        self.assertTrue(PageRevision.objects.filter(
            page=child_page_new, content_json__contains=str(go_live_at.date())).exists()
        )
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new, content_json__contains=str(expire_at.date())).exists()
        )

    def test_edit_scheduled_go_live_before_expiry(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=2)),
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'go_live_at', "Go live date/time must be before expiry date/time")
        self.assertFormError(response, 'form', 'expire_at', "Go live date/time must be before expiry date/time")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_edit_scheduled_expire_in_the_past(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'expire_at': submittable_timestamp(timezone.now() + datetime.timedelta(days=-1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'expire_at', "Expiry date/time must be in the future")

        # form should be marked as having unsaved changes for the purposes of the dirty-forms warning
        self.assertContains(response, "alwaysDirty: true")

    def test_page_edit_post_publish(self):
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Set has_unpublished_changes=True on the existing record to confirm that the publish action
        # is resetting it (and not just leaving it alone)
        self.child_page.has_unpublished_changes = True
        self.child_page.save()

        # Save current value of first_published_at so we can check that it doesn't change
        first_published_at = SimplePage.objects.get(id=self.child_page.id).first_published_at

        # Tests publish from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world-new',
            'action-publish': "Publish",
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data, follow=True
        )

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was edited
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertEqual(child_page_new.title, post_data['title'])
        self.assertEqual(child_page_new.draft_title, post_data['title'])

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], child_page_new.specific_class)
        self.assertEqual(mock_call['instance'], child_page_new)
        self.assertIsInstance(mock_call['instance'], child_page_new.specific_class)

        # The page shouldn't have "has_unpublished_changes" flag set
        self.assertFalse(child_page_new.has_unpublished_changes)

        # first_published_at should not change as it was already set
        self.assertEqual(first_published_at, child_page_new.first_published_at)

        # The "View Live" button should have the updated slug.
        for message in response.context['messages']:
            self.assertIn('hello-world-new', message.message)
            break

    def test_first_published_at_editable(self):
        """Test that we can update the first_published_at via the Page edit form,
        for page models that expose it."""

        # Add child page, of a type which has first_published_at in its form
        child_page = ManyToManyBlogPage(
            title="Hello world!",
            slug="hello-again-world",
            body="hello",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = ManyToManyBlogPage.objects.get(id=child_page.id)

        initial_delta = self.child_page.first_published_at - timezone.now()

        first_published_at = timezone.now() - datetime.timedelta(days=2)

        post_data = {
            'title': "I've been edited!",
            'body': "Some content",
            'slug': 'hello-again-world',
            'action-publish': "Publish",
            'first_published_at': submittable_timestamp(first_published_at),
        }
        self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Get the edited page.
        child_page_new = ManyToManyBlogPage.objects.get(id=self.child_page.id)

        # first_published_at should have changed.
        new_delta = child_page_new.first_published_at - timezone.now()
        self.assertNotEqual(new_delta.days, initial_delta.days)
        # first_published_at should be 3 days ago.
        self.assertEqual(new_delta.days, -3)

    def test_edit_post_publish_scheduled_unpublished_page(self):
        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live anymore
        self.assertFalse(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # The page SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live page yet
        self.assertTrue(
            child_page_new.has_unpublished_changes,
            "A page scheduled for future publishing should have has_unpublished_changes=True"
        )

        self.assertEqual(child_page_new.status_string, "scheduled")

    def test_edit_post_publish_now_an_already_scheduled_unpublished_page(self):
        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        # First let's publish a page with a go_live_at in the future
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live
        self.assertFalse(child_page_new.live)

        self.assertEqual(child_page_new.status_string, "scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # Now, let's edit it and publish it right now
        go_live_at = timezone.now()
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': "",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should be live now
        self.assertTrue(child_page_new.live)

        # And a revision with approved_go_live_at should not exist
        self.assertFalse(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

    def test_edit_post_publish_scheduled_published_page(self):
        # Page is live
        self.child_page.live = True
        self.child_page.save()

        live_revision = self.child_page.live_revision
        original_title = self.child_page.title

        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should still be live
        self.assertTrue(child_page_new.live)

        self.assertEqual(child_page_new.status_string, "live + scheduled")

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        # The page SHOULD have the "has_unpublished_changes" flag set,
        # because the changes are not visible as a live page yet
        self.assertTrue(
            child_page_new.has_unpublished_changes,
            "A page scheduled for future publishing should have has_unpublished_changes=True"
        )

        self.assertNotEqual(
            child_page_new.get_latest_revision(), live_revision,
            "A page scheduled for future publishing should have a new revision, that is not the live revision"
        )

        self.assertEqual(
            child_page_new.title, original_title,
            "A live page with scheduled revisions should still have original content"
        )

    def test_edit_post_publish_now_an_already_scheduled_published_page(self):
        # Unpublish the page
        self.child_page.live = True
        self.child_page.save()

        original_title = self.child_page.title
        # First let's publish a page with a go_live_at in the future
        go_live_at = timezone.now() + datetime.timedelta(days=1)
        expire_at = timezone.now() + datetime.timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should still be live
        self.assertTrue(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        self.assertEqual(
            child_page_new.title, original_title,
            "A live page with scheduled revisions should still have original content"
        )

        # Now, let's edit it and publish it right now
        go_live_at = timezone.now()
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': "",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should be live now
        self.assertTrue(child_page_new.live)

        # And a revision with approved_go_live_at should not exist
        self.assertFalse(
            PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists()
        )

        self.assertEqual(
            child_page_new.title, post_data['title'],
            "A published page should have the new title"
        )

    def test_page_edit_post_submit(self):
        # Create a moderator user for testing email
        get_user_model().objects.create_superuser('moderator', 'moderator@email.com', 'password')

        # Tests submitting from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

        # The latest revision for the page should now be in moderation
        self.assertTrue(child_page_new.get_latest_revision().submitted_for_moderation)

        # Check that the moderator got an email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['moderator@email.com'])
        self.assertEqual(
            mail.outbox[0].subject, 'The page "Hello world!" has been submitted for moderation'
        )  # Note: should this be "I've been edited!"?

    def test_page_edit_post_existing_slug(self):
        # This tests the existing slug checking on page edit

        # Create a page
        self.child_page = SimplePage(title="Hello world 2", slug="hello-world2", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Attempt to change the slug to one thats already in use
        post_data = {
            'title': "Hello world 2",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'slug', "This slug is already in use")

    def test_preview_on_edit(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "I&#39;ve been edited!")

    def test_preview_on_edit_no_session_key(self):
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))

        # get() without corresponding post(), key not set.
        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)

        # We should have an error page because we are unable to
        # preview; the page key was not in the session.
        self.assertContains(
            response,
            "<title>Wagtail - Preview error</title>",
            html=True
        )
        self.assertContains(
            response,
            "<h1>Preview error</h1>",
            html=True
        )

    @modify_settings(ALLOWED_HOSTS={'append': 'childpage.example.com'})
    def test_preview_uses_correct_site(self):
        # create a Site record for the child page
        Site.objects.create(hostname='childpage.example.com', root_page=self.child_page)

        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.child_page.id,))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check that the correct site object has been selected by the site middleware
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertEqual(response.context['request'].site.hostname, 'childpage.example.com')

    def test_editor_picks_up_direct_model_edits(self):
        # If a page has no draft edits, the editor should show the version from the live database
        # record rather than the latest revision record. This ensures that the edit interface
        # reflects any changes made directly on the model.
        self.child_page.title = "This title only exists on the live database record"
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This title only exists on the live database record")

    def test_editor_does_not_pick_up_direct_model_edits_when_draft_edits_exist(self):
        # If a page has draft edits, we should always show those in the editor, not the live
        # database record
        self.child_page.content = "Some content with a draft edit"
        self.child_page.save_revision()

        # make an independent change to the live database record
        self.child_page = SimplePage.objects.get(id=self.child_page.id)
        self.child_page.title = "This title only exists on the live database record"
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "This title only exists on the live database record")
        self.assertContains(response, "Some content with a draft edit")

    def test_editor_page_shows_live_url_in_status_when_draft_edits_exist(self):
        # If a page has draft edits (ie. page has unpublished changes)
        # that affect the URL (eg. slug) we  should still ensure the
        # status button at the top of the page links to the live URL

        self.child_page.content = "Some content with a draft edit"
        self.child_page.slug = "revised-slug-in-draft-only"  # live version contains 'hello-world'
        self.child_page.save_revision()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        link_to_draft = '<a href="/revised-slug-in-draft-only/" target="_blank" rel="noopener noreferrer" class="status-tag primary">live + draft</a>'
        link_to_live = '<a href="/hello-world/" target="_blank" rel="noopener noreferrer" class="status-tag primary">live + draft</a>'
        input_field_for_draft_slug = '<input type="text" name="slug" value="revised-slug-in-draft-only" id="id_slug" maxlength="255" required />'
        input_field_for_live_slug = '<input type="text" name="slug" value="hello-world" id="id_slug" maxlength="255" required />'

        # Status Link should be the live page (not revision)
        self.assertContains(response, link_to_live, html=True)
        self.assertNotContains(response, link_to_draft, html=True)

        # Editing input for slug should be the draft revision
        self.assertContains(response, input_field_for_draft_slug, html=True)
        self.assertNotContains(response, input_field_for_live_slug, html=True)

    def test_editor_page_shows_custom_live_url_in_status_when_draft_edits_exist(self):
        # When showing a live URL in the status button that differs from the draft one,
        # ensure that we pick up any custom URL logic defined on the specific page model

        self.single_event_page.location = "The other side of Mars"
        self.single_event_page.slug = "revised-slug-in-draft-only"  # live version contains 'hello-world'
        self.single_event_page.save_revision()

        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.single_event_page.id, )))

        link_to_draft = '<a href="/revised-slug-in-draft-only/pointless-suffix/" target="_blank" rel="noopener noreferrer" class="status-tag primary">live + draft</a>'
        link_to_live = '<a href="/mars-landing/pointless-suffix/" target="_blank" rel="noopener noreferrer" class="status-tag primary">live + draft</a>'
        input_field_for_draft_slug = '<input type="text" name="slug" value="revised-slug-in-draft-only" id="id_slug" maxlength="255" required />'
        input_field_for_live_slug = '<input type="text" name="slug" value="mars-landing" id="id_slug" maxlength="255" required />'

        # Status Link should be the live page (not revision)
        self.assertContains(response, link_to_live, html=True)
        self.assertNotContains(response, link_to_draft, html=True)

        # Editing input for slug should be the draft revision
        self.assertContains(response, input_field_for_draft_slug, html=True)
        self.assertNotContains(response, input_field_for_live_slug, html=True)

    def test_before_edit_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_edit_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_edit_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_edit_page', hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be edited
        self.assertEqual(Page.objects.get(id=self.child_page.id).title, "Hello world!")

    def test_after_edit_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('after_edit_page', hook_func):
            post_data = {
                'title': "I've been edited!",
                'content': "Some content",
                'slug': 'hello-world-new',
                'action-publish': "Publish",
            }
            response = self.client.post(
                reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be edited
        self.assertEqual(Page.objects.get(id=self.child_page.id).title, "I've been edited!")


class TestPageEditReordering(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add event page
        self.event_page = EventPage(
            title="Event page", slug="event-page",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
        )
        self.event_page.carousel_items = [
            EventPageCarouselItem(caption='1234567', sort_order=1),
            EventPageCarouselItem(caption='7654321', sort_order=2),
            EventPageCarouselItem(caption='abcdefg', sort_order=3),
        ]
        self.root_page.add_child(instance=self.event_page)

        # Login
        self.user = self.login()

    def check_order(self, response, expected_order):
        inline_panel = response.context['edit_handler'].children[0].children[9]
        order = [child.form.instance.caption for child in inline_panel.children]
        self.assertEqual(order, expected_order)

    def test_order(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['1234567', '7654321', 'abcdefg'])

    def test_reorder(self):
        post_data = {
            'title': "Event page",
            'slug': 'event-page',

            'date_from': '01/01/2014',
            'cost': '$10',
            'audience': 'public',
            'location': 'somewhere',

            'related_links-INITIAL_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 1000,
            'related_links-TOTAL_FORMS': 0,

            'speakers-INITIAL_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 1000,
            'speakers-TOTAL_FORMS': 0,

            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 1000,
            'head_counts-TOTAL_FORMS': 0,

            'carousel_items-INITIAL_FORMS': 3,
            'carousel_items-MAX_NUM_FORMS': 1000,
            'carousel_items-TOTAL_FORMS': 3,
            'carousel_items-0-id': self.event_page.carousel_items.all()[0].id,
            'carousel_items-0-caption': self.event_page.carousel_items.all()[0].caption,
            'carousel_items-0-ORDER': 2,
            'carousel_items-1-id': self.event_page.carousel_items.all()[1].id,
            'carousel_items-1-caption': self.event_page.carousel_items.all()[1].caption,
            'carousel_items-1-ORDER': 3,
            'carousel_items-2-id': self.event_page.carousel_items.all()[2].id,
            'carousel_items-2-caption': self.event_page.carousel_items.all()[2].caption,
            'carousel_items-2-ORDER': 1,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )), post_data)

        # Should be redirected back to same page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        # Check order
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])

    def test_reorder_with_validation_error(self):
        post_data = {
            'title': "",  # Validation error
            'slug': 'event-page',

            'date_from': '01/01/2014',
            'cost': '$10',
            'audience': 'public',
            'location': 'somewhere',

            'related_links-INITIAL_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 1000,
            'related_links-TOTAL_FORMS': 0,

            'speakers-INITIAL_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 1000,
            'speakers-TOTAL_FORMS': 0,

            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 1000,
            'head_counts-TOTAL_FORMS': 0,

            'carousel_items-INITIAL_FORMS': 3,
            'carousel_items-MAX_NUM_FORMS': 1000,
            'carousel_items-TOTAL_FORMS': 3,
            'carousel_items-0-id': self.event_page.carousel_items.all()[0].id,
            'carousel_items-0-caption': self.event_page.carousel_items.all()[0].caption,
            'carousel_items-0-ORDER': 2,
            'carousel_items-1-id': self.event_page.carousel_items.all()[1].id,
            'carousel_items-1-caption': self.event_page.carousel_items.all()[1].caption,
            'carousel_items-1-ORDER': 3,
            'carousel_items-2-id': self.event_page.carousel_items.all()[2].id,
            'carousel_items-2-caption': self.event_page.carousel_items.all()[2].caption,
            'carousel_items-2-ORDER': 1,
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.event_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])


class TestPageDelete(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Add a page with child pages of its own
        self.child_index = StandardIndex(title="Hello index", slug='hello-index')
        self.root_page.add_child(instance=self.child_index)
        self.grandchild_page = StandardChild(title="Hello Kitty", slug='hello-kitty')
        self.child_index.add_child(instance=self.grandchild_page)

        # Login
        self.user = self.login()

    def test_page_delete(self):
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)
        # deletion should not actually happen on GET
        self.assertTrue(SimplePage.objects.filter(id=self.child_page.id).exists())

    def test_page_delete_specific_admin_title(self):
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

        # The admin_display_title specific to ChildPage is shown on the delete confirmation page.
        self.assertContains(response, self.child_page.get_admin_display_title())

    def test_page_delete_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get delete page
        response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

        # Check that the deletion has not happened
        self.assertTrue(SimplePage.objects.filter(id=self.child_page.id).exists())

    def test_page_delete_post(self):
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.child_page.specific_class)
        self.assertEqual(mock_call['instance'], self.child_page)
        self.assertIsInstance(mock_call['instance'], self.child_page.specific_class)

    def test_page_delete_notlive_post(self):
        # Same as above, but this makes sure the page_unpublished signal is not fired
        # when if the page is not live when it is deleted

        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was not fired
        self.assertEqual(mock_handler.call_count, 0)

    def test_subpage_deletion(self):
        # Connect mock signal handlers to page_unpublished, pre_delete and post_delete signals
        unpublish_signals_received = []
        pre_delete_signals_received = []
        post_delete_signals_received = []

        def page_unpublished_handler(sender, instance, **kwargs):
            unpublish_signals_received.append((sender, instance.id))

        def pre_delete_handler(sender, instance, **kwargs):
            pre_delete_signals_received.append((sender, instance.id))

        def post_delete_handler(sender, instance, **kwargs):
            post_delete_signals_received.append((sender, instance.id))

        page_unpublished.connect(page_unpublished_handler)
        pre_delete.connect(pre_delete_handler)
        post_delete.connect(post_delete_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_index.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

        # Check that the page is gone
        self.assertFalse(StandardIndex.objects.filter(id=self.child_index.id).exists())
        self.assertFalse(Page.objects.filter(id=self.child_index.id).exists())

        # Check that the subpage is also gone
        self.assertFalse(StandardChild.objects.filter(id=self.grandchild_page.id).exists())
        self.assertFalse(Page.objects.filter(id=self.grandchild_page.id).exists())

        # Check that the signals were fired for both pages
        self.assertIn((StandardIndex, self.child_index.id), unpublish_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), unpublish_signals_received)

        self.assertIn((StandardIndex, self.child_index.id), pre_delete_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), pre_delete_signals_received)

        self.assertIn((StandardIndex, self.child_index.id), post_delete_signals_received)
        self.assertIn((StandardChild, self.grandchild_page.id), post_delete_signals_received)

    def test_before_delete_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_delete_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_delete_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('before_delete_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be deleted
        self.assertTrue(Page.objects.filter(id=self.child_page.id).exists())

    def test_after_delete_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertEqual(page.id, self.child_page.id)

            return HttpResponse("Overridden!")

        with self.register_hook('after_delete_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:delete', args=(self.child_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be deleted
        self.assertFalse(Page.objects.filter(id=self.child_page.id).exists())


class TestPageSearch(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params=None, **extra):
        return self.client.get(reverse('wagtailadmin_pages:search'), params or {}, **extra)

    def test_view(self):
        response = self.get()
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')
        self.assertEqual(response.context['query_string'], "Hello")

    def test_search_searchable_fields(self):
        # Find root page
        root_page = Page.objects.get(id=2)

        # Create a page
        root_page.add_child(instance=SimplePage(
            title="Hi there!", slug='hello-world', content="good morning",
            live=True,
            has_unpublished_changes=False,
        ))

        # Confirm the slug is not being searched
        response = self.get({'q': "hello"})
        self.assertNotContains(response, "There is one matching page")
        search_fields = Page.search_fields

        # Add slug to the search_fields
        Page.search_fields = Page.search_fields + [SearchField('slug', partial_match=True)]

        # Confirm the slug is being searched
        response = self.get({'q': "hello"})
        self.assertContains(response, "There is one matching page")

        # Reset the search fields
        Page.search_fields = search_fields

    def test_ajax(self):
        response = self.get({'q': "Hello"}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'wagtailadmin/pages/search.html')
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search_results.html')
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'q': "Hello", 'p': page})
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')

    def test_root_can_appear_in_search_results(self):
        response = self.get({'q': "roo"})
        self.assertEqual(response.status_code, 200)
        # 'pages' list in the response should contain root
        results = response.context['pages']
        self.assertTrue(any([r.slug == 'root' for r in results]))

    def test_search_uses_admin_display_title_from_specific_class(self):
        # SingleEventPage has a custom get_admin_display_title method; explorer should
        # show the custom title rather than the basic database one
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        root_page.add_child(instance=new_event)
        response = self.get({'q': "lunar"})
        self.assertContains(response, "Lunar event (single event)")

    def test_search_no_perms(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()
        self.assertRedirects(self.get(), '/admin/')

    def test_search_order_by_title(self):
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        root_page.add_child(instance=new_event)

        new_event_2 = SingleEventPage(
            title="A Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        root_page.add_child(instance=new_event_2)

        response = self.get({'q': 'Lunar', 'ordering': 'title'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [new_event_2.id, new_event.id])

        response = self.get({'q': 'Lunar', 'ordering': '-title'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [new_event.id, new_event_2.id])

    def test_search_order_by_updated(self):
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1)
        )
        root_page.add_child(instance=new_event)

        new_event_2 = SingleEventPage(
            title="Lunar event 2",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2015, 1, 1)
        )
        root_page.add_child(instance=new_event_2)

        response = self.get({'q': 'Lunar', 'ordering': 'latest_revision_created_at'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [new_event_2.id, new_event.id])

        response = self.get({'q': 'Lunar', 'ordering': '-latest_revision_created_at'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [new_event.id, new_event_2.id])

    def test_search_order_by_status(self):
        root_page = Page.objects.get(id=2)
        live_event = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1),
            live=True
        )
        root_page.add_child(instance=live_event)

        draft_event = SingleEventPage(
            title="Lunar event",
            location='the moon', audience='public',
            cost='free', date_from='2001-01-01',
            latest_revision_created_at=local_datetime(2016, 1, 1),
            live=False
        )
        root_page.add_child(instance=draft_event)

        response = self.get({'q': 'Lunar', 'ordering': 'live'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [draft_event.id, live_event.id])

        response = self.get({'q': 'Lunar', 'ordering': '-live'})
        page_ids = [page.id for page in response.context['pages']]
        self.assertEqual(page_ids, [live_event.id, draft_event.id])


class TestPageMove(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create three sections
        self.section_a = SimplePage(title="Section A", slug="section-a", content="hello")
        self.root_page.add_child(instance=self.section_a)

        self.section_b = SimplePage(title="Section B", slug="section-b", content="hello")
        self.root_page.add_child(instance=self.section_b)

        self.section_c = SimplePage(title="Section C", slug="section-c", content="hello")
        self.root_page.add_child(instance=self.section_c)

        # Add test page A into section A
        self.test_page_a = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.section_a.add_child(instance=self.test_page_a)

        # Add test page B into section C
        self.test_page_b = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.section_c.add_child(instance=self.test_page_b)

        # Login
        self.user = self.login()

    def test_page_move(self):
        response = self.client.get(reverse('wagtailadmin_pages:move', args=(self.test_page_a.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_move_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get move page
        response = self.client.get(reverse('wagtailadmin_pages:move', args=(self.test_page_a.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_move_confirm(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id))
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_b.id, self.section_a.id))
        )
        # Duplicate slugs triggers a redirect with an error message.
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('wagtailadmin_home'))
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level, message_constants.ERROR)
        # Slug should be in error message.
        self.assertIn("{}".format(self.test_page_b.slug), messages[0].message)

    def test_page_set_page_position(self):
        response = self.client.get(reverse('wagtailadmin_pages:set_page_position', args=(self.test_page_a.id, )))
        self.assertEqual(response.status_code, 200)

    def test_before_move_page_hook(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_move_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_move_page_hook_post(self):
        def hook_func(request, page, destination):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(destination.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_move_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id,
            self.section_a.id
        )

    def test_after_move_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('after_move_page', hook_func):
            response = self.client.post(reverse('wagtailadmin_pages:move_confirm', args=(self.test_page_a.id, self.section_b.id)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be moved
        self.assertEqual(
            Page.objects.get(id=self.test_page_a.id).get_parent().id,
            self.section_b.id
        )


class TestPageCopy(TestCase, WagtailTestUtils):

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page
        self.test_page = self.root_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
            has_unpublished_changes=False,
        ))

        # Create a couple of child pages
        self.test_child_page = self.test_page.add_child(instance=SimplePage(
            title="Child page",
            slug='child-page',
            content="hello",
            live=True,
            has_unpublished_changes=True,
        ))

        self.test_unpublished_child_page = self.test_page.add_child(instance=SimplePage(
            title="Unpublished Child page",
            slug='unpublished-child-page',
            content="hello",
            live=False,
            has_unpublished_changes=True,
        ))

        # Login
        self.user = self.login()

    def test_page_copy(self):
        response = self.client.get(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/copy.html')

        # Make sure all fields are in the form
        self.assertContains(response, "New title")
        self.assertContains(response, "New slug")
        self.assertContains(response, "New parent page")
        self.assertContains(response, "Copy subpages")
        self.assertContains(response, "Publish copies")

    def test_page_copy_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get copy page
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'new_parent_page': str(self.test_page.id),
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # A user with no page permissions at all should be redirected to the admin home
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        # A user with page permissions, but not add permission at the destination,
        # should receive a form validation error
        publishers = Group.objects.create(name='Publishers')
        GroupPagePermission.objects.create(
            group=publishers, page=self.root_page, permission_type='publish'
        )
        self.user.groups.add(publishers)
        self.user.save()

        # Get copy page
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'new_parent_page': str(self.test_page.id),
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue('new_parent_page' in form.errors)

    def test_page_copy_post(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': False,
            'publish_copies': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Get copy
        page_copy = self.root_page.get_children().filter(slug='hello-world-2').first()

        # Check that the copy exists
        self.assertNotEqual(page_copy, None)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)
        self.assertTrue(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were not copied
        self.assertEqual(page_copy.get_children().count(), 0)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_page_copy_post_copy_subpages(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': True,
            'publish_copies': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Get copy
        page_copy = self.root_page.get_children().filter(slug='hello-world-2').first()

        # Check that the copy exists
        self.assertNotEqual(page_copy, None)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)
        self.assertTrue(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the the child pages
        # Neither of them should be live
        child_copy = page_copy.get_children().filter(slug='child-page').first()
        self.assertNotEqual(child_copy, None)
        self.assertFalse(child_copy.live)
        self.assertTrue(child_copy.has_unpublished_changes)

        unpublished_child_copy = page_copy.get_children().filter(slug='unpublished-child-page').first()
        self.assertNotEqual(unpublished_child_copy, None)
        self.assertFalse(unpublished_child_copy.live)
        self.assertTrue(unpublished_child_copy.has_unpublished_changes)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_page_copy_post_copy_subpages_publish_copies(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': True,
            'publish_copies': True,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Get copy
        page_copy = self.root_page.get_children().filter(slug='hello-world-2').first()

        # Check that the copy exists
        self.assertNotEqual(page_copy, None)

        # Check that the copy is live
        self.assertTrue(page_copy.live)
        self.assertFalse(page_copy.has_unpublished_changes)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the the child pages
        # The child_copy should be live but the unpublished_child_copy shouldn't
        child_copy = page_copy.get_children().filter(slug='child-page').first()
        self.assertNotEqual(child_copy, None)
        self.assertTrue(child_copy.live)
        self.assertTrue(child_copy.has_unpublished_changes)

        unpublished_child_copy = page_copy.get_children().filter(slug='unpublished-child-page').first()
        self.assertNotEqual(unpublished_child_copy, None)
        self.assertFalse(unpublished_child_copy.live)
        self.assertTrue(unpublished_child_copy.has_unpublished_changes)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_page_copy_post_new_parent(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'new_parent_page': str(self.test_child_page.id),
            'copy_subpages': False,
            'publish_copies': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the new parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.test_child_page.id, )))

        # Check that the page was copied to the correct place
        self.assertTrue(Page.objects.filter(slug='hello-world-2').first().get_parent(), self.test_child_page)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_page_copy_post_existing_slug_within_same_parent_page(self):
        # This tests the existing slug checking on page copy when not changing the parent page

        # Attempt to copy the page but forget to change the slug
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response,
            'form',
            'new_slug',
            "This slug is already in use within the context of its parent page \"Welcome to your new Wagtail site!\""
        )

    def test_page_copy_post_and_subpages_to_same_tree_branch(self):
        # This tests that a page cannot be copied into itself when copying subpages
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'new_parent_page': str(self.test_child_page.id),
            'copy_subpages': True,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id,)), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response, 'form', 'new_parent_page', "You cannot copy a page into itself when copying subpages"
        )

    def test_page_copy_post_existing_slug_to_another_parent_page(self):
        # This tests the existing slug checking on page copy when changing the parent page

        # Attempt to copy the page and changed the parent page
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'new_parent_page': str(self.test_child_page.id),
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.test_child_page.id, )))

    def test_page_copy_post_invalid_slug(self):
        # Attempt to copy the page but set an invalid slug string
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello world!',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(
            response, 'form', 'new_slug', "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens."
        )

    def test_page_copy_no_publish_permission(self):
        # Turn user into an editor who can add pages but not publish them
        self.user.is_superuser = False
        self.user.groups.add(
            Group.objects.get(name="Editors"),
        )
        self.user.save()

        # Get copy page
        response = self.client.get(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )))

        # The user should have access to the copy page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/copy.html')

        # Make sure the "publish copies" field is hidden
        self.assertNotContains(response, "Publish copies")

    def test_page_copy_no_publish_permission_post_copy_subpages_publish_copies(self):
        # This tests that unprivileged users cannot publish copied pages even if they hack their browser

        # Turn user into an editor who can add pages but not publish them
        self.user.is_superuser = False
        self.user.groups.add(
            Group.objects.get(name="Editors"),
        )
        self.user.save()

        # Post
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'new_parent_page': str(self.root_page.id),
            'copy_subpages': True,
            'publish_copies': True,
        }
        response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id, )), post_data)

        # Check that the user was redirected to the parents explore page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Get copy
        page_copy = self.root_page.get_children().filter(slug='hello-world-2').first()

        # Check that the copy exists
        self.assertNotEqual(page_copy, None)

        # Check that the copy is not live
        self.assertFalse(page_copy.live)

        # Check that the owner of the page is set correctly
        self.assertEqual(page_copy.owner, self.user)

        # Check that the children were copied
        self.assertEqual(page_copy.get_children().count(), 2)

        # Check the the child pages
        # Neither of them should be live
        child_copy = page_copy.get_children().filter(slug='child-page').first()
        self.assertNotEqual(child_copy, None)
        self.assertFalse(child_copy.live)

        unpublished_child_copy = page_copy.get_children().filter(slug='unpublished-child-page').first()
        self.assertNotEqual(unpublished_child_copy, None)
        self.assertFalse(unpublished_child_copy.live)

        # treebeard should report no consistency problems with the tree
        self.assertFalse(any(Page.find_problems()), 'treebeard found consistency problems')

    def test_before_copy_page_hook(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_copy_page', hook_func):
            response = self.client.get(reverse('wagtailadmin_pages:copy', args=(self.test_page.id,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

    def test_before_copy_page_hook_post(self):
        def hook_func(request, page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('before_copy_page', hook_func):
            post_data = {
                'new_title': "Hello world 2",
                'new_slug': 'hello-world-2',
                'new_parent_page': str(self.root_page.id),
                'copy_subpages': False,
                'publish_copies': False,
            }
            response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id,)), post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should not be copied
        self.assertFalse(Page.objects.filter(title="Hello world 2").exists())

    def test_after_copy_page_hook(self):
        def hook_func(request, page, new_page):
            self.assertIsInstance(request, HttpRequest)
            self.assertIsInstance(page.specific, SimplePage)
            self.assertIsInstance(new_page.specific, SimplePage)

            return HttpResponse("Overridden!")

        with self.register_hook('after_copy_page', hook_func):
            post_data = {
                'new_title': "Hello world 2",
                'new_slug': 'hello-world-2',
                'new_parent_page': str(self.root_page.id),
                'copy_subpages': False,
                'publish_copies': False,
            }
            response = self.client.post(reverse('wagtailadmin_pages:copy', args=(self.test_page.id,)), post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Overridden!")

        # page should be copied
        self.assertTrue(Page.objects.filter(title="Hello world 2").exists())


class TestPageUnpublish(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        # Create a page to unpublish
        self.root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
        )
        self.root_page.add_child(instance=self.page)

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')

    def test_unpublish_view_invalid_page_id(self):
        """
        This tests that the unpublish view returns an error if the page id is invalid
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unpublish_view_bad_permissions(self):
        """
        This tests that the unpublish view doesn't allow users without unpublish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished
        """
        # Connect a mock signal handler to page_unpublished signal
        mock_handler = mock.MagicMock()
        page_unpublished.connect(mock_handler)

        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.page.id).live)

        # Check that the page_unpublished signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.page.specific_class)
        self.assertEqual(mock_call['instance'], self.page)
        self.assertIsInstance(mock_call['instance'], self.page.specific_class)

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that does not contain the form field 'include_descendants'
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')
        # Check the form does not contain the checkbox field include_descendants
        self.assertNotContains(response, '<input id="id_include_descendants" name="include_descendants" type="checkbox">')


class TestPageUnpublishIncludingDescendants(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page to unpublish
        self.test_page = self.root_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=True,
            has_unpublished_changes=False,
        ))

        # Create a couple of child pages
        self.test_child_page = self.test_page.add_child(instance=SimplePage(
            title="Child page",
            slug='child-page',
            content="hello",
            live=True,
            has_unpublished_changes=True,
        ))

        self.test_another_child_page = self.test_page.add_child(instance=SimplePage(
            title="Another Child page",
            slug='another-child-page',
            content="hello",
            live=True,
            has_unpublished_changes=True,
        ))

    def test_unpublish_descendants_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page that contains the form field 'include_descendants'
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )))

        # Check that the user received an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')
        # Check the form contains the checkbox field include_descendants
        self.assertContains(response, '<input id="id_include_descendants" name="include_descendants" type="checkbox">')

    def test_unpublish_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page and its descendants were unpublished
        """
        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )), {'include_descendants': 'on'})

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.test_page.id).live)

        # Check that the descendant pages were unpiblished as well
        self.assertFalse(SimplePage.objects.get(id=self.test_child_page.id).live)
        self.assertFalse(SimplePage.objects.get(id=self.test_another_child_page.id).live)

    def test_unpublish_not_include_children_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished but its descendants were not
        """
        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages:unpublish', args=(self.test_page.id, )), {})

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.test_page.id).live)

        # Check that the descendant pages were not unpublished
        self.assertTrue(SimplePage.objects.get(id=self.test_child_page.id).live)
        self.assertTrue(SimplePage.objects.get(id=self.test_another_child_page.id).live)


class TestApproveRejectModeration(TestCase, WagtailTestUtils):
    def setUp(self):
        self.submitter = get_user_model().objects.create_superuser(
            username='submitter',
            email='submitter@email.com',
            password='password',
        )

        self.user = self.login()

        # Create a page and submit it for moderation
        root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
            has_unpublished_changes=True,
        )
        root_page.add_child(instance=self.page)

        self.page.save_revision(user=self.submitter, submitted_for_moderation=True)
        self.revision = self.page.get_latest_revision()

    def test_approve_moderation_view(self):
        """
        This posts to the approve moderation view and checks that the page was approved
        """
        # Connect a mock signal handler to page_published signal
        mock_handler = mock.MagicMock()
        page_published.connect(mock_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page should now have no unpublished changes
        self.assertFalse(
            page.has_unpublished_changes,
            "Approving moderation failed to set has_unpublished_changes=False"
        )

        # Check that the page_published signal was fired
        self.assertEqual(mock_handler.call_count, 1)
        mock_call = mock_handler.mock_calls[0][2]

        self.assertEqual(mock_call['sender'], self.page.specific_class)
        self.assertEqual(mock_call['instance'], self.page)
        self.assertIsInstance(mock_call['instance'], self.page.specific_class)

    def test_approve_moderation_when_later_revision_exists(self):
        self.page.title = "Goodbye world!"
        self.page.save_revision(user=self.submitter, submitted_for_moderation=False)

        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page content should be the submitted version, not the published one
        self.assertEqual(page.title, "Hello world!")
        # Page should still have unpublished changes
        self.assertTrue(
            page.has_unpublished_changes,
            "has_unpublished_changes incorrectly cleared on approve_moderation when a later revision exists"
        )

    def test_approve_moderation_view_bad_revision_id(self):
        """
        This tests that the approve moderation view handles invalid revision ids correctly
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_approve_moderation_view_bad_permissions(self):
        """
        This tests that the approve moderation view doesn't allow users without moderation permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_reject_moderation_view(self):
        """
        This posts to the reject moderation view and checks that the page was rejected
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        # Page must not be live
        self.assertFalse(Page.objects.get(id=self.page.id).live)

        # Revision must no longer be submitted for moderation
        self.assertFalse(PageRevision.objects.get(id=self.revision.id).submitted_for_moderation)

    def test_reject_moderation_view_bad_revision_id(self):
        """
        This tests that the reject moderation view handles invalid revision ids correctly
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(12345, )))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_reject_moderation_view_bad_permissions(self):
        """
        This tests that the reject moderation view doesn't allow users without moderation permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Post
        response = self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_preview_for_moderation(self):
        response = self.client.get(reverse('wagtailadmin_pages:preview_for_moderation', args=(self.revision.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "Hello world!")


class TestContentTypeUse(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()

    def test_content_type_use(self):
        # Get use of event page
        response = self.client.get(reverse('wagtailadmin_pages:type_use', args=('tests', 'eventpage')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/content_type_use.html')
        self.assertContains(response, "Christmas")


class TestSubpageBusinessRules(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add standard page (allows subpages of any type)
        self.standard_index = StandardIndex()
        self.standard_index.title = "Standard Index"
        self.standard_index.slug = "standard-index"
        self.root_page.add_child(instance=self.standard_index)

        # Add business page (allows BusinessChild and BusinessSubIndex as subpages)
        self.business_index = BusinessIndex()
        self.business_index.title = "Business Index"
        self.business_index.slug = "business-index"
        self.root_page.add_child(instance=self.business_index)

        # Add business child (allows no subpages)
        self.business_child = BusinessChild()
        self.business_child.title = "Business Child"
        self.business_child.slug = "business-child"
        self.business_index.add_child(instance=self.business_child)

        # Add business subindex (allows only BusinessChild as subpages)
        self.business_subindex = BusinessSubIndex()
        self.business_subindex.title = "Business Subindex"
        self.business_subindex.slug = "business-subindex"
        self.business_index.add_child(instance=self.business_subindex)

        # Login
        self.login()

    def test_standard_subpage(self):
        add_subpage_url = reverse('wagtailadmin_pages:add_subpage', args=(self.standard_index.id, ))

        # explorer should contain a link to 'add child page'
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.standard_index.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, add_subpage_url)

        # add_subpage should give us choices of StandardChild, and BusinessIndex.
        # BusinessSubIndex and BusinessChild are not allowed
        response = self.client.get(add_subpage_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, StandardChild.get_verbose_name())
        self.assertContains(response, BusinessIndex.get_verbose_name())
        self.assertNotContains(response, BusinessSubIndex.get_verbose_name())
        self.assertNotContains(response, BusinessChild.get_verbose_name())

    def test_business_subpage(self):
        add_subpage_url = reverse('wagtailadmin_pages:add_subpage', args=(self.business_index.id, ))

        # explorer should contain a link to 'add child page'
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.business_index.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, add_subpage_url)

        # add_subpage should give us a cut-down set of page types to choose
        response = self.client.get(add_subpage_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, StandardIndex.get_verbose_name())
        self.assertNotContains(response, StandardChild.get_verbose_name())
        self.assertContains(response, BusinessSubIndex.get_verbose_name())
        self.assertContains(response, BusinessChild.get_verbose_name())

    def test_business_child_subpage(self):
        add_subpage_url = reverse('wagtailadmin_pages:add_subpage', args=(self.business_child.id, ))

        # explorer should not contain a link to 'add child page', as this page doesn't accept subpages
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.business_child.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, add_subpage_url)

        # this also means that fetching add_subpage is blocked at the permission-check level
        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(self.business_child.id, )))
        self.assertEqual(response.status_code, 403)

    def test_cannot_add_invalid_subpage_type(self):
        # cannot add StandardChild as a child of BusinessIndex, as StandardChild is not present in subpage_types
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardchild', self.business_index.id))
        )
        self.assertEqual(response.status_code, 403)

        # likewise for BusinessChild which has an empty subpage_types list
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardchild', self.business_child.id))
        )
        self.assertEqual(response.status_code, 403)

        # cannot add BusinessChild to StandardIndex, as BusinessChild restricts is parent page types
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'businesschild', self.standard_index.id))
        )
        self.assertEqual(response.status_code, 403)

        # but we can add a BusinessChild to BusinessIndex
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'businesschild', self.business_index.id))
        )
        self.assertEqual(response.status_code, 200)

    def test_not_prompted_for_page_type_when_only_one_choice(self):
        response = self.client.get(reverse('wagtailadmin_pages:add_subpage', args=(self.business_subindex.id, )))
        # BusinessChild is the only valid subpage type of BusinessSubIndex, so redirect straight there
        self.assertRedirects(
            response, reverse('wagtailadmin_pages:add', args=('tests', 'businesschild', self.business_subindex.id))
        )


class TestNotificationPreferences(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

        # Create two moderator users for testing 'submitted' email
        User = get_user_model()
        self.moderator = User.objects.create_superuser('moderator', 'moderator@email.com', 'password')
        self.moderator2 = User.objects.create_superuser('moderator2', 'moderator2@email.com', 'password')

        # Create a submitter for testing 'rejected' and 'approved' emails
        self.submitter = User.objects.create_user('submitter', 'submitter@email.com', 'password')

        # User profiles for moderator2 and the submitter
        self.moderator2_profile = UserProfile.get_for_user(self.moderator2)
        self.submitter_profile = UserProfile.get_for_user(self.submitter)

        # Create a page and submit it for moderation
        self.child_page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.child_page)

        # POST data to edit the page
        self.post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }

    def submit(self):
        return self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), self.post_data)

    def silent_submit(self):
        """
        Sets up the child_page as needing moderation, without making a request
        """
        self.child_page.save_revision(user=self.submitter, submitted_for_moderation=True)
        self.revision = self.child_page.get_latest_revision()

    def approve(self):
        return self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(self.revision.id, )))

    def reject(self):
        return self.client.post(reverse('wagtailadmin_pages:reject_moderation', args=(self.revision.id, )))

    def test_vanilla_profile(self):
        # Check that the vanilla profile has rejected notifications on
        self.assertEqual(self.submitter_profile.rejected_notifications, True)

        # Check that the vanilla profile has approved notifications on
        self.assertEqual(self.submitter_profile.approved_notifications, True)

    def test_submit_notifications_sent(self):
        # Submit
        self.submit()

        # Check that both the moderators got an email, and no others
        self.assertEqual(len(mail.outbox), 2)
        email_to = mail.outbox[0].to + mail.outbox[1].to
        self.assertIn(self.moderator.email, email_to)
        self.assertIn(self.moderator2.email, email_to)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(len(mail.outbox[1].to), 1)

    def test_submit_notification_preferences_respected(self):
        # moderator2 doesn't want emails
        self.moderator2_profile.submitted_notifications = False
        self.moderator2_profile.save()

        # Submit
        self.submit()

        # Check that only one moderator got an email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual([self.moderator.email], mail.outbox[0].to)

    def test_approved_notifications(self):
        # Set up the page version
        self.silent_submit()
        # Approve
        self.approve()

        # Submitter must receive an approved email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['submitter@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "Hello world!" has been approved')

    def test_approved_notifications_preferences_respected(self):
        # Submitter doesn't want 'approved' emails
        self.submitter_profile.approved_notifications = False
        self.submitter_profile.save()

        # Set up the page version
        self.silent_submit()
        # Approve
        self.approve()

        # No email to send
        self.assertEqual(len(mail.outbox), 0)

    def test_rejected_notifications(self):
        # Set up the page version
        self.silent_submit()
        # Reject
        self.reject()

        # Submitter must receive a rejected email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['submitter@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "Hello world!" has been rejected')

    def test_rejected_notification_preferences_respected(self):
        # Submitter doesn't want 'rejected' emails
        self.submitter_profile.rejected_notifications = False
        self.submitter_profile.save()

        # Set up the page version
        self.silent_submit()
        # Reject
        self.reject()

        # No email to send
        self.assertEqual(len(mail.outbox), 0)

    def test_moderator_group_notifications(self):
        # Create a (non-superuser) moderator
        User = get_user_model()
        user1 = User.objects.create_user('moduser1', 'moduser1@email.com')
        user1.groups.add(Group.objects.get(name='Moderators'))
        user1.save()

        # Create another group and user with permission to moderate
        modgroup2 = Group.objects.create(name='More moderators')
        GroupPagePermission.objects.create(
            group=modgroup2, page=self.root_page, permission_type='publish'
        )
        user2 = User.objects.create_user('moduser2', 'moduser2@email.com')
        user2.groups.add(Group.objects.get(name='More moderators'))
        user2.save()

        # Submit
        # This used to break in Wagtail 1.3 (Postgres exception, SQLite 3/4 notifications)
        response = self.submit()

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the superusers and the moderation group members all got an email
        expected_emails = 4
        self.assertEqual(len(mail.outbox), expected_emails)
        email_to = []
        for i in range(expected_emails):
            self.assertEqual(len(mail.outbox[i].to), 1)
            email_to += mail.outbox[i].to
        self.assertIn(self.moderator.email, email_to)
        self.assertIn(self.moderator2.email, email_to)
        self.assertIn(user1.email, email_to)
        self.assertIn(user2.email, email_to)

    @override_settings(WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS=False)
    def test_disable_superuser_notification(self):
        # Add one of the superusers to the moderator group
        self.moderator.groups.add(Group.objects.get(name='Moderators'))

        response = self.submit()

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the non-moderator superuser is not being notified
        expected_emails = 1
        self.assertEqual(len(mail.outbox), expected_emails)
        # Use chain as the 'to' field is a list of recipients
        email_to = list(chain.from_iterable([m.to for m in mail.outbox]))
        self.assertIn(self.moderator.email, email_to)
        self.assertNotIn(self.moderator2.email, email_to)

    @mock.patch.object(EmailMultiAlternatives, 'send', side_effect=IOError('Server down'))
    def test_email_send_error(self, mock_fn):
        logging.disable(logging.CRITICAL)
        # Approve
        self.silent_submit()
        response = self.approve()
        logging.disable(logging.NOTSET)

        # An email that fails to send should return a message rather than crash the page
        self.assertEqual(response.status_code, 302)
        response = self.client.get(reverse('wagtailadmin_home'))

        # There should be one "approved" message and one "failed to send notifications"
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].level, message_constants.SUCCESS)
        self.assertEqual(messages[1].level, message_constants.ERROR)

    def test_email_headers(self):
        # Submit
        self.submit()

        msg_headers = set(mail.outbox[0].message().items())
        headers = {('Auto-Submitted', 'auto-generated')}
        self.assertTrue(headers.issubset(msg_headers), msg='Message is missing the Auto-Submitted header.',)


class TestLocking(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

        # Create a page and submit it for moderation
        self.child_page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.child_page)

    def test_lock_post(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_get(self):
        response = self.client.get(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_already_locked(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_with_good_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages:edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_with_bad_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )), {
            'next': 'http://www.google.co.uk'
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_bad_page(self):
        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(9999, )))

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.post(reverse('wagtailadmin_pages:lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_get(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_already_unlocked(self):
        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_good_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages:edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_bad_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )), {
            'next': 'http://www.google.co.uk'
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_bad_page(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(9999, )))

        # Check response
        self.assertEqual(response.status_code, 404)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages:unlock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)


class TestIssue197(TestCase, WagtailTestUtils):
    def test_issue_197(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a tagged page with no tags
        self.tagged_page = self.root_page.add_child(instance=TaggedPage(
            title="Tagged page",
            slug='tagged-page',
            live=False,
        ))

        # Login
        self.user = self.login()

        # Add some tags and publish using edit view
        post_data = {
            'title': "Tagged page",
            'slug': 'tagged-page',
            'tags': "hello, world",
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.tagged_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that both tags are in the pages tag set
        page = TaggedPage.objects.get(id=self.tagged_page.id)
        self.assertIn('hello', page.tags.slugs())
        self.assertIn('world', page.tags.slugs())


class TestChildRelationsOnSuperclass(TestCase, WagtailTestUtils):
    # In our test models we define AdvertPlacement as a child relation on the Page model.
    # Here we check that this behaves correctly when exposed on the edit form of a Page
    # subclass (StandardIndex here).
    fixtures = ['test.json']

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)
        self.test_advert = Advert.objects.get(id=1)

        # Add child page
        self.index_page = StandardIndex(
            title="My lovely index",
            slug="my-lovely-index",
            advert_placements=[AdvertPlacement(advert=self.test_advert)]
        )
        self.root_page.add_child(instance=self.index_page)

        # Login
        self.login()

    def test_get_create_form(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id))
        )
        self.assertEqual(response.status_code, 200)
        # Response should include an advert_placements formset labelled Adverts
        self.assertContains(response, "Adverts")
        self.assertContains(response, "id_advert_placements-TOTAL_FORMS")

    def test_post_create_form(self):
        post_data = {
            'title': "New index!",
            'slug': 'new-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '0',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': 'yellow',
            'advert_placements-0-id': '',
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id)), post_data
        )

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='new-index').specific

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(page.id, )))

        self.assertEqual(page.advert_placements.count(), 1)
        self.assertEqual(page.advert_placements.first().advert.text, 'test_advert')

    def test_post_create_form_with_validation_error_in_formset(self):
        post_data = {
            'title': "New index!",
            'slug': 'new-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '0',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': '',  # should fail as colour is a required field
            'advert_placements-0-id': '',
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'standardindex', self.root_page.id)), post_data
        )

        # Should remain on the edit page with a validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        # form should be marked as having unsaved changes
        self.assertContains(response, "alwaysDirty: true")

    def test_get_edit_form(self):
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Response should include an advert_placements formset labelled Adverts
        self.assertContains(response, "Adverts")
        self.assertContains(response, "id_advert_placements-TOTAL_FORMS")
        # the formset should be populated with an existing form
        self.assertContains(response, "id_advert_placements-0-advert")
        self.assertContains(
            response, '<option value="1" selected="selected">test_advert</option>', html=True
        )

    def test_post_edit_form(self):
        post_data = {
            'title': "My lovely index",
            'slug': 'my-lovely-index',
            'advert_placements-TOTAL_FORMS': '2',
            'advert_placements-INITIAL_FORMS': '1',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': 'yellow',
            'advert_placements-0-id': self.index_page.advert_placements.first().id,
            'advert_placements-1-advert': '1',
            'advert_placements-1-colour': 'purple',
            'advert_placements-1-id': '',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Find the page and check it
        page = Page.objects.get(id=self.index_page.id).specific
        self.assertEqual(page.advert_placements.count(), 2)
        self.assertEqual(page.advert_placements.all()[0].advert.text, 'test_advert')
        self.assertEqual(page.advert_placements.all()[1].advert.text, 'test_advert')

    def test_post_edit_form_with_validation_error_in_formset(self):
        post_data = {
            'title': "My lovely index",
            'slug': 'my-lovely-index',
            'advert_placements-TOTAL_FORMS': '1',
            'advert_placements-INITIAL_FORMS': '1',
            'advert_placements-MAX_NUM_FORMS': '1000',
            'advert_placements-0-advert': '1',
            'advert_placements-0-colour': '',
            'advert_placements-0-id': self.index_page.advert_placements.first().id,
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.index_page.id, )), post_data)

        # Should remain on the edit page with a validation error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")
        # form should be marked as having unsaved changes
        self.assertContains(response, "alwaysDirty: true")


class TestRevisions(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path='/home/events/christmas/')
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = '2013-12-25'
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = '2014-12-25'
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.login()

    def test_edit_form_has_revisions_link(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_event.id, ))
        )
        self.assertEqual(response.status_code, 200)
        revisions_index_url = reverse(
            'wagtailadmin_pages:revisions_index', args=(self.christmas_event.id, )
        )
        self.assertContains(response, revisions_index_url)

    def test_get_revisions_index(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:revisions_index', args=(self.christmas_event.id, ))
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, formats.localize(parse_date('2013-12-25')))
        last_christmas_preview_url = reverse(
            'wagtailadmin_pages:revisions_view',
            args=(self.christmas_event.id, self.last_christmas_revision.id)
        )
        last_christmas_revert_url = reverse(
            'wagtailadmin_pages:revisions_revert',
            args=(self.christmas_event.id, self.last_christmas_revision.id)
        )
        self.assertContains(response, last_christmas_preview_url)
        self.assertContains(response, last_christmas_revert_url)

        self.assertContains(response, formats.localize(local_datetime(2014, 12, 25)))
        this_christmas_preview_url = reverse(
            'wagtailadmin_pages:revisions_view',
            args=(self.christmas_event.id, self.this_christmas_revision.id)
        )
        this_christmas_revert_url = reverse(
            'wagtailadmin_pages:revisions_revert',
            args=(self.christmas_event.id, self.this_christmas_revision.id)
        )
        self.assertContains(response, this_christmas_preview_url)
        self.assertContains(response, this_christmas_revert_url)

    def test_preview_revision(self):
        last_christmas_preview_url = reverse(
            'wagtailadmin_pages:revisions_view',
            args=(self.christmas_event.id, self.last_christmas_revision.id)
        )
        response = self.client.get(last_christmas_preview_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Last Christmas I gave you my heart")

    def test_revert_revision(self):
        last_christmas_preview_url = reverse(
            'wagtailadmin_pages:revisions_revert',
            args=(self.christmas_event.id, self.last_christmas_revision.id)
        )
        response = self.client.get(last_christmas_preview_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Editing Event page")
        self.assertContains(response, "You are viewing a previous revision of this page")

        # Form should show the content of the revision, not the current draft
        self.assertContains(response, "Last Christmas I gave you my heart")

        # Form should include a hidden 'revision' field
        revision_field = (
            """<input type="hidden" name="revision" value="%d" />""" %
            self.last_christmas_revision.id
        )
        self.assertContains(response, revision_field)

        # Buttons should be relabelled
        self.assertContains(response, "Replace current draft")
        self.assertContains(response, "Publish this revision")

    def test_scheduled_revision(self):
        self.last_christmas_revision.publish()
        self.this_christmas_revision.approved_go_live_at = local_datetime(2014, 12, 26)
        self.this_christmas_revision.save()
        this_christmas_unschedule_url = reverse(
            'wagtailadmin_pages:revisions_unschedule',
            args=(self.christmas_event.id, self.this_christmas_revision.id)
        )
        response = self.client.get(
            reverse('wagtailadmin_pages:revisions_index', args=(self.christmas_event.id, ))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scheduled for')
        self.assertContains(response, formats.localize(parse_date('2014-12-26')))
        self.assertContains(response, this_christmas_unschedule_url)


class TestCompareRevisions(TestCase, WagtailTestUtils):
    # Actual tests for the comparison classes can be found in test_compare.py

    fixtures = ['test.json']

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path='/home/events/christmas/')
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = '2013-12-25'
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = '2014-12-25'
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.login()

    def test_compare_revisions(self):
        compare_url = reverse(
            'wagtailadmin_pages:revisions_compare',
            args=(self.christmas_event.id, self.last_christmas_revision.id, self.this_christmas_revision.id)
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>')

    def test_compare_revisions_earliest(self):
        compare_url = reverse(
            'wagtailadmin_pages:revisions_compare',
            args=(self.christmas_event.id, 'earliest', self.this_christmas_revision.id)
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>')

    def test_compare_revisions_latest(self):
        compare_url = reverse(
            'wagtailadmin_pages:revisions_compare',
            args=(self.christmas_event.id, self.last_christmas_revision.id, 'latest')
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll give it to someone special</span>')

    def test_compare_revisions_live(self):
        # Mess with the live version, bypassing revisions
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll just feed it to the dog</p>"
        )
        self.christmas_event.save(update_fields=['body'])

        compare_url = reverse(
            'wagtailadmin_pages:revisions_compare',
            args=(self.christmas_event.id, self.last_christmas_revision.id, 'live')
        )
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, '<span class="deletion">Last Christmas I gave you my heart, but the very next day you gave it away</span><span class="addition">This year, to save me from tears, I&#39;ll just feed it to the dog</span>')


class TestCompareRevisionsWithNonModelField(TestCase, WagtailTestUtils):
    """
    Tests if form fields defined in the base_form_class will not be included.
    in revisions view as they are not actually on the model.
    Flagged in issue #3737
    Note: Actual tests for comparison classes can be found in test_compare.py
    """

    fixtures = ['test.json']
    # FormClassAdditionalFieldPage

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page of class with base_form_class override
        # non model field is 'code'
        self.test_page = FormClassAdditionalFieldPage(
            title='A Statement',
            slug='a-statement',
            location='Early Morning Cafe, Mainland, NZ',
            body="<p>hello</p>"
        )
        self.root_page.add_child(instance=self.test_page)

        # add new revision
        self.test_page.title = 'Statement'
        self.test_page.location = 'Victory Monument, Bangkok'
        self.test_page.body = (
            "<p>I would like very much to go into the forrest.</p>"
        )
        self.test_page_revision = self.test_page.save_revision()
        self.test_page_revision.created_at = local_datetime(2017, 10, 15)
        self.test_page_revision.save()

        # add another new revision
        self.test_page.title = 'True Statement'
        self.test_page.location = 'Victory Monument, Bangkok'
        self.test_page.body = (
            "<p>I would like very much to go into the forest.</p>"
        )
        self.test_page_revision_new = self.test_page.save_revision()
        self.test_page_revision_new.created_at = local_datetime(2017, 10, 16)
        self.test_page_revision_new.save()

        self.login()

    def test_base_form_class_used(self):
        """First ensure that the non-model field is appearing in edit."""
        edit_url = reverse('wagtailadmin_pages:add', args=('tests', 'formclassadditionalfieldpage', self.test_page.id))
        response = self.client.get(edit_url)
        self.assertContains(response, '<input type="text" name="code" required id="id_code" maxlength="5" />', html=True)

    def test_compare_revisions(self):
        """Confirm that the non-model field is not shown in revision."""
        compare_url = reverse(
            'wagtailadmin_pages:revisions_compare',
            args=(self.test_page.id, self.test_page_revision.id, self.test_page_revision_new.id)
        )
        response = self.client.get(compare_url)
        self.assertContains(response, '<span class="deletion">forrest.</span><span class="addition">forest.</span>')
        # should not contain the field defined in the formclass used
        self.assertNotContains(response, '<h2>Code:</h2>')


class TestRevisionsUnschedule(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.christmas_event = EventPage.objects.get(url_path='/home/events/christmas/')
        self.christmas_event.title = "Last Christmas"
        self.christmas_event.date_from = '2013-12-25'
        self.christmas_event.body = (
            "<p>Last Christmas I gave you my heart, "
            "but the very next day you gave it away</p>"
        )
        self.last_christmas_revision = self.christmas_event.save_revision()
        self.last_christmas_revision.created_at = local_datetime(2013, 12, 25)
        self.last_christmas_revision.save()
        self.last_christmas_revision.publish()

        self.christmas_event.title = "This Christmas"
        self.christmas_event.date_from = '2014-12-25'
        self.christmas_event.body = (
            "<p>This year, to save me from tears, "
            "I'll give it to someone special</p>"
        )
        self.this_christmas_revision = self.christmas_event.save_revision()
        self.this_christmas_revision.created_at = local_datetime(2014, 12, 24)
        self.this_christmas_revision.save()

        self.this_christmas_revision.approved_go_live_at = local_datetime(2014, 12, 25)
        self.this_christmas_revision.save()

        self.user = self.login()

    def test_unschedule_view(self):
        """
        This tests that the unschedule view responds with a confirm page
        """
        response = self.client.get(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.christmas_event.id, self.this_christmas_revision.id)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/revisions/confirm_unschedule.html')

    def test_unschedule_view_invalid_page_id(self):
        """
        This tests that the unschedule view returns an error if the page id is invalid
        """
        # Get unschedule page
        response = self.client.get(reverse('wagtailadmin_pages:revisions_unschedule', args=(12345, 67894)))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unschedule_view_invalid_revision_id(self):
        """
        This tests that the unschedule view returns an error if the page id is invalid
        """
        # Get unschedule page
        response = self.client.get(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.christmas_event.id, 67894)))

        # Check that the user received a 404 response
        self.assertEqual(response.status_code, 404)

    def test_unschedule_view_bad_permissions(self):
        """
        This tests that the unschedule view doesn't allow users without publish permissions
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get unschedule page
        response = self.client.get(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.christmas_event.id, self.this_christmas_revision.id)))

        # Check that the user received a 403 response
        self.assertEqual(response.status_code, 403)

    def test_unschedule_view_post(self):
        """
        This posts to the unschedule view and checks that the revision was unscheduled
        """

        # Post to the unschedule page
        response = self.client.post(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.christmas_event.id, self.this_christmas_revision.id)))

        # Should be redirected to revisions index page
        self.assertRedirects(response, reverse('wagtailadmin_pages:revisions_index', args=(self.christmas_event.id, )))

        # Check that the page has no approved_schedule
        self.assertFalse(EventPage.objects.get(id=self.christmas_event.id).approved_schedule)

        # Check that the approved_go_live_at has been cleared from the revision
        self.assertIsNone(self.christmas_event.revisions.get(id=self.this_christmas_revision.id).approved_go_live_at)


class TestRevisionsUnscheduleForUnpublishedPages(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.unpublished_event = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        self.unpublished_event.title = "Unpublished Page"
        self.unpublished_event.date_from = '2014-12-25'
        self.unpublished_event.body = (
            "<p>Some Content</p>"
        )
        self.unpublished_revision = self.unpublished_event.save_revision()
        self.unpublished_revision.created_at = local_datetime(2014, 12, 25)
        self.unpublished_revision.save()

        self.user = self.login()

    def test_unschedule_view(self):
        """
        This tests that the unschedule view responds with a confirm page
        """
        response = self.client.get(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.unpublished_event.id, self.unpublished_revision.id)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/revisions/confirm_unschedule.html')

    def test_unschedule_view_post(self):
        """
        This posts to the unschedule view and checks that the revision was unscheduled
        """

        # Post to the unschedule page
        response = self.client.post(reverse('wagtailadmin_pages:revisions_unschedule', args=(self.unpublished_event.id, self.unpublished_revision.id)))

        # Should be redirected to revisions index page
        self.assertRedirects(response, reverse('wagtailadmin_pages:revisions_index', args=(self.unpublished_event.id, )))

        # Check that the page has no approved_schedule
        self.assertFalse(EventPage.objects.get(id=self.unpublished_event.id).approved_schedule)

        # Check that the approved_go_live_at has been cleared from the revision
        self.assertIsNone(self.unpublished_event.revisions.get(id=self.unpublished_revision.id).approved_go_live_at)


class TestIssue2599(TestCase, WagtailTestUtils):
    """
    When previewing a page on creation, we need to assign it a path value consistent with its
    (future) position in the tree. The naive way of doing this is to give it an index number
    one more than numchild - however, index numbers are not reassigned on page deletion, so
    this can result in a path that collides with an existing page (which is invalid).
    """

    def test_issue_2599(self):
        homepage = Page.objects.get(id=2)

        child1 = Page(title='child1')
        homepage.add_child(instance=child1)
        child2 = Page(title='child2')
        homepage.add_child(instance=child2)

        child1.delete()

        self.login()
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        preview_url = reverse('wagtailadmin_pages:preview_on_add',
                              args=('tests', 'simplepage', homepage.id))
        response = self.client.post(preview_url, post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "New page!")

        # Check that the treebeard attributes were set correctly on the page object
        self.assertEqual(response.context['self'].depth, homepage.depth + 1)
        self.assertTrue(response.context['self'].path.startswith(homepage.path))
        self.assertEqual(response.context['self'].get_parent(), homepage)


class TestIssue2492(TestCase, WagtailTestUtils):
    """
    The publication submission message generation was performed using
    the Page class, as opposed to the specific_class for that Page.
    This test ensures that the specific_class url method is called
    when the 'view live' message button is created.
    """

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        child_page = SingleEventPage(
            title="Test Event", slug="test-event", location="test location",
            cost="10", date_from=datetime.datetime.now(),
            audience=EVENT_AUDIENCE_CHOICES[0][0])
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SingleEventPage.objects.get(id=child_page.id)
        self.user = self.login()

    def test_page_edit_post_publish_url(self):
        post_data = {
            'action-publish': "Publish",
            'title': self.child_page.title,
            'date_from': self.child_page.date_from,
            'slug': self.child_page.slug,
            'audience': self.child_page.audience,
            'location': self.child_page.location,
            'cost': self.child_page.cost,
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )),
            post_data, follow=True)

        # Grab a fresh copy's URL
        new_url = SingleEventPage.objects.get(id=self.child_page.id).url

        # The "View Live" button should have the custom URL.
        for message in response.context['messages']:
            self.assertIn('"{}"'.format(new_url), message.message)
            break


class TestIssue3982(TestCase, WagtailTestUtils):
    """
    Pages that are not associated with a site, and thus do not have a live URL,
    should not display a "View live" link in the flash message after being
    edited.
    """

    def setUp(self):
        super().setUp()
        self.login()

    def _create_page(self, parent):
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', parent.pk)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world', 'action-publish': "publish"},
            follow=True)
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(parent.pk,)))
        page = SimplePage.objects.get()
        self.assertTrue(page.live)
        return response, page

    def test_create_accessible(self):
        """
        Create a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._create_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_create_inaccessible(self):
        """
        Create a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._create_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))

    def _edit_page(self, parent):
        page = parent.add_child(instance=SimplePage(title='Hello, world!', content='Some content'))
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(page.pk,)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world', 'action-publish': "publish"},
            follow=True)
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(parent.pk,)))
        page = SimplePage.objects.get(pk=page.pk)
        self.assertTrue(page.live)
        return response, page

    def test_edit_accessible(self):
        """
        Edit a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._edit_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_edit_inaccessible(self):
        """
        Edit a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._edit_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))

    def _approve_page(self, parent):
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', parent.pk)),
            {'title': "Hello, world!", 'content': "Some content", 'slug': 'hello-world', 'action-submit': "submit"},
            follow=True)
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(parent.pk,)))
        page = SimplePage.objects.get()
        self.assertFalse(page.live)
        revision = PageRevision.objects.get(page=page)
        response = self.client.post(reverse('wagtailadmin_pages:approve_moderation', args=(revision.pk,)), follow=True)
        page = SimplePage.objects.get()
        self.assertTrue(page.live)
        self.assertRedirects(response, reverse('wagtailadmin_home'))
        return response, page

    def test_approve_accessible(self):
        """
        Edit a page under the site root, check the flash message has a valid
        "View live" button.
        """
        response, page = self._approve_page(Page.objects.get(pk=2))
        self.assertIsNotNone(page.url)
        self.assertTrue(any(
            'View live' in message.message and page.url in message.message
            for message in response.context['messages']))

    def test_approve_inaccessible(self):
        """
        Edit a page outside of the site root, check the flash message does
        not have a "View live" button.
        """
        response, page = self._approve_page(Page.objects.get(pk=1))
        self.assertIsNone(page.url)
        self.assertFalse(any(
            'View live' in message.message
            for message in response.context['messages']))


class TestInlinePanelMedia(TestCase, WagtailTestUtils):
    """
    Test that form media required by InlinePanels is correctly pulled in to the edit page
    """

    def test_inline_panel_media(self):
        homepage = Page.objects.get(id=2)
        self.login()

        # simplepage does not need draftail...
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'wagtailadmin/js/draftail.js')

        # but sectionedrichtextpage does
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'sectionedrichtextpage', homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'wagtailadmin/js/draftail.js')


class TestInlineStreamField(TestCase, WagtailTestUtils):
    """
    Test that streamfields inside an inline child work
    """

    def test_inline_streamfield(self):
        homepage = Page.objects.get(id=2)
        self.login()

        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'inlinestreampage', homepage.id)))
        self.assertEqual(response.status_code, 200)

        # response should include HTML declarations for streamfield child blocks
        self.assertContains(response, '<li id="__PREFIX__-container" class="sequence-member">')


class TestRecentEditsPanel(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="Some content here",
        )
        self.root_page.add_child(instance=child_page)
        child_page.save_revision().publish()
        self.child_page = SimplePage.objects.get(id=child_page.id)

        get_user_model().objects.create_superuser(username='alice', email='alice@email.com', password='password')
        get_user_model().objects.create_superuser(username='bob', email='bob@email.com', password='password')

    def change_something(self, title):
        post_data = {'title': title, 'content': "Some content", 'slug': 'hello-world'}
        response = self.client.post(reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.child_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

    def go_to_dashboard_response(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        return response

    def test_your_recent_edits(self):
        # Login as Bob
        self.client.login(username='bob', password='password')

        # Bob hasn't edited anything yet
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertNotIn('Your most recent edits', response.content.decode('utf-8'))

        # Login as Alice
        self.client.logout()
        self.client.login(username='alice', password='password')

        # Alice changes something
        self.change_something("Alice's edit")

        # Edit should show up on dashboard
        response = self.go_to_dashboard_response()
        self.assertIn('Your most recent edits', response.content.decode('utf-8'))

        # Bob changes something
        self.client.login(username='bob', password='password')
        self.change_something("Bob's edit")

        # Edit shows up on Bobs dashboard
        response = self.go_to_dashboard_response()
        self.assertIn('Your most recent edits', response.content.decode('utf-8'))

        # Login as Alice again
        self.client.logout()
        self.client.login(username='alice', password='password')

        # Alice's dashboard should still list that first edit
        response = self.go_to_dashboard_response()
        self.assertIn('Your most recent edits', response.content.decode('utf-8'))

    def test_panel(self):
        """Test if the panel actually returns expected pages """
        self.client.login(username='bob', password='password')
        # change a page
        self.change_something("Bob's edit")
        # set a user to 'mock' a request
        self.client.user = get_user_model().objects.get(email='bob@email.com')
        # get the panel to get the last edits
        panel = RecentEditsPanel(self.client)
        # check if the revision is the revision of edited Page
        self.assertEqual(panel.last_edits[0][0].page, Page.objects.get(pk=self.child_page.id))
        # check if the page in this list is the specific page of this revision
        self.assertEqual(panel.last_edits[0][1], Page.objects.get(pk=self.child_page.id).specific)


class TestIssue2994(TestCase, WagtailTestUtils):
    """
    In contrast to most "standard" form fields, StreamField form widgets generally won't
    provide a postdata field with a name exactly matching the field name. To prevent Django
    from wrongly interpreting this as the field being omitted from the form,
    we need to provide a custom value_omitted_from_data method.
    """

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.user = self.login()

    def test_page_edit_post_publish_url(self):
        # Post
        post_data = {
            'title': "Issue 2994 test",
            'slug': 'issue-2994-test',
            'body-count': '1',
            'body-0-deleted': '',
            'body-0-order': '0',
            'body-0-type': 'text',
            'body-0-value': 'hello world',
            'action-publish': "Publish",
        }
        self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'defaultstreampage', self.root_page.id)), post_data
        )
        new_page = DefaultStreamPage.objects.get(slug='issue-2994-test')
        self.assertEqual(1, len(new_page.body))
        self.assertEqual('hello world', new_page.body[0].value)


class TestParentalM2M(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_index = Page.objects.get(url_path='/home/events/')
        self.christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        self.user = self.login()
        self.holiday_category = EventCategory.objects.create(name='Holiday')
        self.men_with_beards_category = EventCategory.objects.create(name='Men with beards')

    def test_create_and_save(self):
        post_data = {
            'title': "Presidents' Day",
            'date_from': "2017-02-20",
            'slug': "presidents-day",
            'audience': "public",
            'location': "America",
            'cost': "$1",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'eventpage', self.events_index.id)),
            post_data
        )
        created_page = EventPage.objects.get(url_path='/home/events/presidents-day/')
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(created_page.id, )))
        created_revision = created_page.get_latest_revision_as_page()

        self.assertIn(self.holiday_category, created_revision.categories.all())
        self.assertIn(self.men_with_beards_category, created_revision.categories.all())

    def test_create_and_publish(self):
        post_data = {
            'action-publish': "Publish",
            'title': "Presidents' Day",
            'date_from': "2017-02-20",
            'slug': "presidents-day",
            'audience': "public",
            'location': "America",
            'cost': "$1",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:add', args=('tests', 'eventpage', self.events_index.id)),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.events_index.id, )))

        created_page = EventPage.objects.get(url_path='/home/events/presidents-day/')
        self.assertIn(self.holiday_category, created_page.categories.all())
        self.assertIn(self.men_with_beards_category, created_page.categories.all())

    def test_edit_and_save(self):
        post_data = {
            'title': "Christmas",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )))
        updated_page = EventPage.objects.get(id=self.christmas_page.id)
        created_revision = updated_page.get_latest_revision_as_page()

        self.assertIn(self.holiday_category, created_revision.categories.all())
        self.assertIn(self.men_with_beards_category, created_revision.categories.all())

        # no change to live page record yet
        self.assertEqual(0, updated_page.categories.count())

    def test_edit_and_publish(self):
        post_data = {
            'action-publish': "Publish",
            'title': "Christmas",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.holiday_category.id, self.men_with_beards_category.id]
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.events_index.id, )))
        updated_page = EventPage.objects.get(id=self.christmas_page.id)
        self.assertEqual(2, updated_page.categories.count())
        self.assertIn(self.holiday_category, updated_page.categories.all())
        self.assertIn(self.men_with_beards_category, updated_page.categories.all())


class TestValidationErrorMessages(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_index = Page.objects.get(url_path='/home/events/')
        self.christmas_page = Page.objects.get(url_path='/home/events/christmas/')
        self.user = self.login()

    def test_field_error(self):
        """Field errors should be shown against the relevant fields, not in the header message"""
        post_data = {
            'title': "",
            'date_from': "2017-12-25",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        # the error should only appear once: against the field, not in the header message
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""", count=1, html=True)
        self.assertContains(response, "This field is required", count=1)

    def test_non_field_error(self):
        """Non-field errors should be shown in the header message"""
        post_data = {
            'title': "Christmas",
            'date_from': "2017-12-25",
            'date_to': "2017-12-24",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        self.assertContains(response, "<li>The end date must be after the start date</li>", count=1)

    def test_field_and_non_field_error(self):
        """
        If both field and non-field errors exist, all errors should be shown in the header message
        with appropriate context to identify the field; and field errors should also be shown
        against the relevant fields.
        """
        post_data = {
            'title': "",
            'date_from': "2017-12-25",
            'date_to': "2017-12-24",
            'slug': "christmas",
            'audience': "public",
            'location': "The North Pole",
            'cost': "Free",
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
        }
        response = self.client.post(
            reverse('wagtailadmin_pages:edit', args=(self.christmas_page.id, )),
            post_data
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "The page could not be saved due to validation errors")
        self.assertContains(response, "<li>The end date must be after the start date</li>", count=1)

        # Error on title shown against the title field
        self.assertContains(response, """<p class="error-message"><span>This field is required.</span></p>""", count=1, html=True)
        # Error on title shown in the header message
        self.assertContains(response, "<li>Title: This field is required.</li>", count=1)


class TestDraftAccess(TestCase, WagtailTestUtils):
    """Tests for the draft view access restrictions."""

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)

        # create user with admin access (but not draft_view access)
        user = get_user_model().objects.create_user(username='bob', email='bob@email.com', password='password')
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )

    def test_draft_access_admin(self):
        """Test that admin can view draft."""
        # Login as admin
        self.user = self.login()

        # Try getting page draft
        response = self.client.get(reverse('wagtailadmin_pages:view_draft', args=(self.child_page.id, )))

        # User can view
        self.assertEqual(response.status_code, 200)

    def test_draft_access_unauthorized(self):
        """Test that user without edit/publish permission can't view draft."""
        self.assertTrue(self.client.login(username='bob', password='password'))

        # Try getting page draft
        response = self.client.get(reverse('wagtailadmin_pages:view_draft', args=(self.child_page.id, )))

        # User gets Unauthorized response
        self.assertEqual(response.status_code, 403)

    def test_draft_access_authorized(self):
        """Test that user with edit permission can view draft."""
        # give user the permission to edit page
        user = get_user_model().objects.get(username='bob')
        user.groups.add(Group.objects.get(name='Moderators'))
        user.save()

        self.assertTrue(self.client.login(username='bob', password='password'))

        # Get add subpage page
        response = self.client.get(reverse('wagtailadmin_pages:view_draft', args=(self.child_page.id, )))

        # User can view
        self.assertEqual(response.status_code, 200)


class TestPreview(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.meetings_category = EventCategory.objects.create(name='Meetings')
        self.parties_category = EventCategory.objects.create(name='Parties')
        self.holidays_category = EventCategory.objects.create(name='Holidays')

        self.home_page = Page.objects.get(url_path='/home/')
        self.event_page = Page.objects.get(url_path='/home/events/christmas/')

        self.user = self.login()

        self.post_data = {
            'title': "Beach party",
            'slug': 'beach-party',
            'body': '''{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "party on wayne", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}''',
            'date_from': '2017-08-01',
            'audience': 'public',
            'location': 'the beach',
            'cost': 'six squid',
            'carousel_items-TOTAL_FORMS': 0,
            'carousel_items-INITIAL_FORMS': 0,
            'carousel_items-MIN_NUM_FORMS': 0,
            'carousel_items-MAX_NUM_FORMS': 0,
            'speakers-TOTAL_FORMS': 0,
            'speakers-INITIAL_FORMS': 0,
            'speakers-MIN_NUM_FORMS': 0,
            'speakers-MAX_NUM_FORMS': 0,
            'related_links-TOTAL_FORMS': 0,
            'related_links-INITIAL_FORMS': 0,
            'related_links-MIN_NUM_FORMS': 0,
            'related_links-MAX_NUM_FORMS': 0,
            'head_counts-TOTAL_FORMS': 0,
            'head_counts-INITIAL_FORMS': 0,
            'head_counts-MIN_NUM_FORMS': 0,
            'head_counts-MAX_NUM_FORMS': 0,
            'categories': [self.parties_category.id, self.holidays_category.id],
        }

    def test_preview_on_create_with_m2m_field(self):
        preview_url = reverse('wagtailadmin_pages:preview_on_add',
                              args=('tests', 'eventpage', self.home_page.id))
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/event_page.html')
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_with_m2m_field(self):
        preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                              args=(self.event_page.id,))
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        response = self.client.get(preview_url)

        # Check the HTML response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/event_page.html')
        self.assertContains(response, "Beach party")
        self.assertContains(response, "<li>Parties</li>")
        self.assertContains(response, "<li>Holidays</li>")

    def test_preview_on_edit_expiry(self):
        initial_datetime = timezone.now()
        expiry_datetime = initial_datetime + datetime.timedelta(
            seconds=PreviewOnEdit.preview_expiration_timeout + 1)

        with freeze_time(initial_datetime) as frozen_datetime:
            preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                                  args=(self.event_page.id,))
            response = self.client.post(preview_url, self.post_data)

            # Check the JSON response
            self.assertEqual(response.status_code, 200)

            response = self.client.get(preview_url)

            # Check the HTML response
            self.assertEqual(response.status_code, 200)

            frozen_datetime.move_to(expiry_datetime)

            preview_url = reverse('wagtailadmin_pages:preview_on_edit',
                                  args=(self.home_page.id,))
            response = self.client.post(preview_url, self.post_data)
            self.assertEqual(response.status_code, 200)
            response = self.client.get(preview_url)
            self.assertEqual(response.status_code, 200)
