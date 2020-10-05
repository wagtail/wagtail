from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import paginator
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin.tests.pages.timestamps import local_datetime
from wagtail.core.models import GroupPagePermission, Locale, Page
from wagtail.tests.testapp.models import SimplePage, SingleEventPage, StandardIndex
from wagtail.tests.utils import WagtailTestUtils


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

    def test_construct_page_listing_buttons_hook(self):
        # testapp implements a construct_page_listing_buttons hook
        # that add's an dummy button with the label 'Dummy Button' which points
        # to '/dummy-button'
        response = self.client.get(
            reverse('wagtailadmin_explore', args=(self.root_page.id, )),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertContains(response, 'Dummy Button')
        self.assertContains(response, '/dummy-button')

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
        expected = """
            <li>
                <a href="%s"><span class="title">Secret plans (simple page)</span>
                    <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-arrow-right"></use>
                    </svg>
                </a>
            </li>
        """ % expected_url
        self.assertContains(response, expected, html=True)


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
        self.login(username='superuser', password='password')
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
        self.login(username='superuser', password='password')
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
        self.login(username='superuser', password='password')
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
        self.login(username='siteeditor', password='password')
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
        self.login(username='siteeditor', password='password')
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
        self.login(username='siteeditor', password='password')
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.site_page.id, )))
        self.assertEqual(response.status_code, 200)
        # There should be no warning message here
        self.assertNotContains(response, "Pages created here will not be accessible")

    # Tests for users that have explore permission *somewhere*, but not at the view being tested;
    # in all cases, they should be redirected to their explorable root

    def test_bad_permissions_at_root(self):
        # 'siteeditor' does not have permission to explore the root
        self.login(username='siteeditor', password='password')
        response = self.client.get(reverse('wagtailadmin_explore_root'))

        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response['Location']),
            (302, reverse('wagtailadmin_explore', args=(self.site_page.pk, )))
        )

    def test_bad_permissions_at_non_site_page(self):
        # 'siteeditor' does not have permission to explore no_site_page
        self.login(username='siteeditor', password='password')
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
        self.login(username='siteeditor', password='password')
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
        self.login(username='superman', password='password')
        for page in Page.objects.all():
            response = self.client.get(reverse('wagtailadmin_explore', args=[page.pk]))
            self.assertEqual(response.status_code, 200)

    def test_admin_sees_root_page_as_explorer_root(self):
        self.login(username='superman', password='password')
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)
        # Administrator should see the full list of children of the Root page.
        self.assertContains(response, "Welcome to testserver!")
        self.assertContains(response, "Welcome to example.com!")

    def test_admin_sees_breadcrumbs_up_to_root_page(self):
        self.login(username='superman', password='password')
        response = self.client.get(reverse('wagtailadmin_explore', args=[6]))
        self.assertEqual(response.status_code, 200)
        expected = """
            <li class="home">
                <a href="/admin/pages/">
                    <svg class="icon icon-site home_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-site"></use>
                    </svg>
                    <span class="visuallyhidden">Root</span>
                    <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-arrow-right"></use>
                    </svg>
                </a>
            </li>
        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li>
                <a href="/admin/pages/4/">
                    <span class="title">Welcome to example.com!</span>
                    <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-arrow-right"></use>
                    </svg>
                </a>
            </li>
        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li>
                <a href="/admin/pages/5/">
                    <span class="title">Content</span>
                    <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-arrow-right"></use>
                    </svg>
                </a>
            </li>
        """
        self.assertContains(response, expected, html=True)

    def test_nonadmin_sees_breadcrumbs_up_to_cca(self):
        self.login(username='josh', password='password')
        response = self.client.get(reverse('wagtailadmin_explore', args=[6]))
        self.assertEqual(response.status_code, 200)
        # While at "Page 1", Josh should see the breadcrumbs leading only as far back as the example.com homepage,
        # since it's his Closest Common Ancestor.
        expected = """
            <li class="home">
                <a href="/admin/pages/4/" class="text-replace">
                    <svg class="icon icon-site home_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-site"></use>
                    </svg>
                    <span class="visuallyhidden">Home</span>
                </a>
                <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li>
                <a href="/admin/pages/5/">
                    <span class="title">Content</span>
                    <svg class="icon icon-arrow-right arrow_right_icon" aria-hidden="true" focusable="false">
                        <use href="#icon-arrow-right"></use>
                    </svg>
                </a>
            </li>
        """
        self.assertContains(response, expected, html=True)
        # The page title shouldn't appear because it's the "home" breadcrumb.
        self.assertNotContains(response, "Welcome to example.com!")

    def test_admin_home_page_changes_with_permissions(self):
        self.login(username='bob', password='password')
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # Bob should only see the welcome for example.com, not testserver
        self.assertContains(response, "Welcome to the example.com Wagtail CMS")
        self.assertNotContains(response, "testserver")

    def test_breadcrumb_with_no_user_permissions(self):
        self.login(username='mary', password='password')
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)
        # Since Mary has no page permissions, she should not see the breadcrumb
        self.assertNotContains(response, """<li class="home"><a href="/admin/pages/4/" class="icon icon-home text-replace">Home</a></li>""")


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.events_page = Page.objects.get(url_path='/home/events/')
        self.fr_locale = Locale.objects.create(language_code='fr')
        self.translated_events_page = self.events_page.copy_for_translation(self.fr_locale, copy_parents=True)
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=[self.events_page.id])
        )

        self.assertContains(response, '<li class="header-meta--locale">')

        add_translation_url = reverse('wagtailadmin_explore', args=[self.translated_events_page.id])
        self.assertContains(response, f'<a href="{add_translation_url}" aria-label="French" class="u-link is-live">')

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse('wagtailadmin_explore', args=[self.events_page.id])
        )

        self.assertNotContains(response, '<li class="header-meta--locale">')

        add_translation_url = reverse('wagtailadmin_explore', args=[self.translated_events_page.id])
        self.assertNotContains(response, f'<a href="{add_translation_url}" aria-label="French" class="u-link is-live">')
