from django.test import TestCase, Client
from django.http import HttpRequest, Http404

from django.contrib.auth.models import User

from wagtail.wagtailcore.models import Page, Site, UserPagePermissionsProxy
from wagtail.tests.models import EventPage, EventIndex, SimplePage


class TestRouting(TestCase):
    fixtures = ['test.json']

    def test_find_site_for_request(self):
        default_site = Site.objects.get(is_default_site=True)
        events_page = Page.objects.get(url_path='/home/events/')
        events_site = Site.objects.create(hostname='events.example.com', root_page=events_page)

        # requests without a Host: header should be directed to the default site
        request = HttpRequest()
        request.path = '/'
        self.assertEqual(Site.find_for_request(request), default_site)

        # requests with a known Host: header should be directed to the specific site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = 'events.example.com'
        self.assertEqual(Site.find_for_request(request), events_site)

        # requests with an unrecognised Host: header should be directed to the default site
        request = HttpRequest()
        request.path = '/'
        request.META['HTTP_HOST'] = 'unknown.example.com'
        self.assertEqual(Site.find_for_request(request), default_site)

    def test_urls(self):
        default_site = Site.objects.get(is_default_site=True)
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = Page.objects.get(url_path='/home/events/christmas/')

        # Basic installation only has one site configured, so page.url will return local URLs
        self.assertEqual(homepage.full_url, 'http://localhost/')
        self.assertEqual(homepage.url, '/')
        self.assertEqual(homepage.relative_url(default_site), '/')

        self.assertEqual(christmas_page.full_url, 'http://localhost/events/christmas/')
        self.assertEqual(christmas_page.url, '/events/christmas/')
        self.assertEqual(christmas_page.relative_url(default_site), '/events/christmas/')

    def test_urls_with_multiple_sites(self):
        events_page = Page.objects.get(url_path='/home/events/')
        events_site = Site.objects.create(hostname='events.example.com', root_page=events_page)

        default_site = Site.objects.get(is_default_site=True)
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = Page.objects.get(url_path='/home/events/christmas/')

        # with multiple sites, page.url will return full URLs to ensure that
        # they work across sites
        self.assertEqual(homepage.full_url, 'http://localhost/')
        self.assertEqual(homepage.url, 'http://localhost/')
        self.assertEqual(homepage.relative_url(default_site), '/')
        self.assertEqual(homepage.relative_url(events_site), 'http://localhost/')

        self.assertEqual(christmas_page.full_url, 'http://events.example.com/christmas/')
        self.assertEqual(christmas_page.url, 'http://events.example.com/christmas/')
        self.assertEqual(christmas_page.relative_url(default_site), 'http://events.example.com/christmas/')
        self.assertEqual(christmas_page.relative_url(events_site), '/christmas/')

    def test_request_routing(self):
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

        request = HttpRequest()
        request.path = '/events/christmas/'
        response = homepage.route(request, ['events', 'christmas'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['self'], christmas_page)
        used_template = response.resolve_template(response.template_name)
        self.assertEqual(used_template.name, 'tests/event_page.html')

    def test_route_to_unknown_page_returns_404(self):
        homepage = Page.objects.get(url_path='/home/')

        request = HttpRequest()
        request.path = '/events/quinquagesima/'
        with self.assertRaises(Http404):
            homepage.route(request, ['events', 'quinquagesima'])

    def test_route_to_unpublished_page_returns_404(self):
        homepage = Page.objects.get(url_path='/home/')

        request = HttpRequest()
        request.path = '/events/tentative-unpublished-event/'
        with self.assertRaises(Http404):
            homepage.route(request, ['events', 'tentative-unpublished-event'])


class TestServeView(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        # Explicitly clear the cache of site root paths. Normally this would be kept
        # in sync by the Site.save logic, but this is bypassed when the database is
        # rolled back between tests using transactions.
        from django.core.cache import cache
        cache.delete('wagtail_site_root_paths')

    def test_serve(self):
        response = self.client.get('/events/christmas/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'tests/event_page.html')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(response.context['self'], christmas_page)

        self.assertContains(response, '<h1>Christmas</h1>')
        self.assertContains(response, '<h2>Event</h2>')

    def test_serve_unknown_page_returns_404(self):
        response = self.client.get('/events/quinquagesima/')
        self.assertEqual(response.status_code, 404)

    def test_serve_unpublished_page_returns_404(self):
        response = self.client.get('/events/tentative-unpublished-event/')
        self.assertEqual(response.status_code, 404)

    def test_serve_with_multiple_sites(self):
        events_page = Page.objects.get(url_path='/home/events/')
        Site.objects.create(hostname='events.example.com', root_page=events_page)

        response = self.client.get('/christmas/', HTTP_HOST='events.example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'tests/event_page.html')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(response.context['self'], christmas_page)

        self.assertContains(response, '<h1>Christmas</h1>')
        self.assertContains(response, '<h2>Event</h2>')

        # same request to the default host should return a 404
        c = Client()
        response = c.get('/christmas/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 404)

    def test_serve_with_custom_context(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

        # should render the whole page
        self.assertContains(response, '<h1>Events</h1>')

        # response should contain data from the custom 'events' context variable
        self.assertContains(response, '<a href="/events/christmas/">Christmas</a>')

    def test_ajax_response(self):
        response = self.client.get('/events/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        # should only render the content of includes/event_listing.html, not the whole page
        self.assertNotContains(response, '<h1>Events</h1>')
        self.assertContains(response, '<a href="/events/christmas/">Christmas</a>')


class TestPageUrlTags(TestCase):
    fixtures = ['test.json']

    def test_pageurl_tag(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="/events/christmas/">Christmas</a>')

    def test_slugurl_tag(self):
        response = self.client.get('/events/christmas/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<a href="/events/">Back to events index</a>')


class TestPagePermission(TestCase):
    fixtures = ['test.json']

    def test_nonpublisher_page_permissions(self):
        event_editor = User.objects.get(username='eventeditor')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        homepage_perms = homepage.permissions_for_user(event_editor)
        christmas_page_perms = christmas_page.permissions_for_user(event_editor)
        unpub_perms = unpublished_event_page.permissions_for_user(event_editor)
        someone_elses_event_perms = someone_elses_event_page.permissions_for_user(event_editor)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())
        self.assertTrue(someone_elses_event_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())
        self.assertFalse(someone_elses_event_perms.can_edit())  # basic 'add' permission doesn't allow editing pages owned by someone else

        self.assertFalse(homepage_perms.can_delete())
        self.assertFalse(christmas_page_perms.can_delete())  # cannot delete because it is published
        self.assertTrue(unpub_perms.can_delete())
        self.assertFalse(someone_elses_event_perms.can_delete())

        self.assertFalse(homepage_perms.can_publish())
        self.assertFalse(christmas_page_perms.can_publish())
        self.assertFalse(unpub_perms.can_publish())

        self.assertFalse(homepage_perms.can_unpublish())
        self.assertFalse(christmas_page_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())

        self.assertFalse(homepage_perms.can_publish_subpage())
        self.assertFalse(christmas_page_perms.can_publish_subpage())
        self.assertFalse(unpub_perms.can_publish_subpage())

        self.assertFalse(homepage_perms.can_reorder_children())
        self.assertFalse(christmas_page_perms.can_reorder_children())
        self.assertFalse(unpub_perms.can_reorder_children())

        self.assertFalse(homepage_perms.can_move())
        self.assertFalse(christmas_page_perms.can_move())  # cannot move because this would involve unpublishing from its current location
        self.assertTrue(unpub_perms.can_move())
        self.assertFalse(someone_elses_event_perms.can_move())

        self.assertFalse(christmas_page_perms.can_move_to(unpublished_event_page))  # cannot move because this would involve unpublishing from its current location
        self.assertTrue(unpub_perms.can_move_to(christmas_page))
        self.assertFalse(unpub_perms.can_move_to(homepage))  # no permission to create pages at destination
        self.assertFalse(unpub_perms.can_move_to(unpublished_event_page))  # cannot make page a child of itself


    def test_publisher_page_permissions(self):
        event_moderator = User.objects.get(username='eventmoderator')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')

        homepage_perms = homepage.permissions_for_user(event_moderator)
        christmas_page_perms = christmas_page.permissions_for_user(event_moderator)
        unpub_perms = unpublished_event_page.permissions_for_user(event_moderator)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())

        self.assertFalse(homepage_perms.can_delete())
        self.assertTrue(christmas_page_perms.can_delete())  # cannot delete because it is published
        self.assertTrue(unpub_perms.can_delete())

        self.assertFalse(homepage_perms.can_publish())
        self.assertTrue(christmas_page_perms.can_publish())
        self.assertTrue(unpub_perms.can_publish())

        self.assertFalse(homepage_perms.can_unpublish())
        self.assertTrue(christmas_page_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())  # cannot unpublish a page that isn't published

        self.assertFalse(homepage_perms.can_publish_subpage())
        self.assertTrue(christmas_page_perms.can_publish_subpage())
        self.assertTrue(unpub_perms.can_publish_subpage())

        self.assertFalse(homepage_perms.can_reorder_children())
        self.assertTrue(christmas_page_perms.can_reorder_children())
        self.assertTrue(unpub_perms.can_reorder_children())

        self.assertFalse(homepage_perms.can_move())
        self.assertTrue(christmas_page_perms.can_move())
        self.assertTrue(unpub_perms.can_move())

        self.assertTrue(christmas_page_perms.can_move_to(unpublished_event_page))
        self.assertTrue(unpub_perms.can_move_to(christmas_page))
        self.assertFalse(unpub_perms.can_move_to(homepage))  # no permission to create pages at destination
        self.assertFalse(unpub_perms.can_move_to(unpublished_event_page))  # cannot make page a child of itself

    def test_inactive_user_has_no_permissions(self):
        user = User.objects.get(username='inactiveuser')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')

        christmas_page_perms = christmas_page.permissions_for_user(user)
        unpub_perms = unpublished_event_page.permissions_for_user(user)

        self.assertFalse(unpub_perms.can_add_subpage())
        self.assertFalse(unpub_perms.can_edit())
        self.assertFalse(unpub_perms.can_delete())
        self.assertFalse(unpub_perms.can_publish())
        self.assertFalse(christmas_page_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_publish_subpage())
        self.assertFalse(unpub_perms.can_reorder_children())
        self.assertFalse(unpub_perms.can_move())
        self.assertFalse(unpub_perms.can_move_to(christmas_page))

    def test_superuser_has_full_permissions(self):
        user = User.objects.get(username='superuser')
        homepage = Page.objects.get(url_path='/home/')
        root = Page.objects.get(url_path='/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')

        homepage_perms = homepage.permissions_for_user(user)
        root_perms = root.permissions_for_user(user)
        unpub_perms = unpublished_event_page.permissions_for_user(user)

        self.assertTrue(homepage_perms.can_add_subpage())
        self.assertTrue(root_perms.can_add_subpage())

        self.assertTrue(homepage_perms.can_edit())
        self.assertFalse(root_perms.can_edit())  # root is not a real editable page, even to superusers

        self.assertTrue(homepage_perms.can_delete())
        self.assertFalse(root_perms.can_delete())

        self.assertTrue(homepage_perms.can_publish())
        self.assertFalse(root_perms.can_publish())

        self.assertTrue(homepage_perms.can_unpublish())
        self.assertFalse(root_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())

        self.assertTrue(homepage_perms.can_publish_subpage())
        self.assertTrue(root_perms.can_publish_subpage())

        self.assertTrue(homepage_perms.can_reorder_children())
        self.assertTrue(root_perms.can_reorder_children())

        self.assertTrue(homepage_perms.can_move())
        self.assertFalse(root_perms.can_move())

        self.assertTrue(homepage_perms.can_move_to(root))
        self.assertFalse(homepage_perms.can_move_to(unpublished_event_page))

    def test_editable_pages_for_user_with_add_permission(self):
        event_editor = User.objects.get(username='eventeditor')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        editable_pages = UserPagePermissionsProxy(event_editor).editable_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

    def test_editable_pages_for_user_with_edit_permission(self):
        event_moderator = User.objects.get(username='eventmoderator')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        editable_pages = UserPagePermissionsProxy(event_moderator).editable_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())

    def test_editable_pages_for_inactive_user(self):
        user = User.objects.get(username='inactiveuser')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        editable_pages = UserPagePermissionsProxy(user).editable_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertFalse(editable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

    def test_editable_pages_for_superuser(self):
        user = User.objects.get(username='superuser')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        editable_pages = UserPagePermissionsProxy(user).editable_pages()

        self.assertTrue(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())


class TestPageQuerySet(TestCase):
    fixtures = ['test.json']

    def test_live(self):
        pages = Page.objects.live()

        # All pages must be live
        for page in pages:
            self.assertTrue(page.live)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())

    def test_not_live(self):
        pages = Page.objects.not_live()

        # All pages must not be live
        for page in pages:
            self.assertFalse(page.live)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path='/home/events/someone-elses-event/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_page(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.page(homepage)

        # Should only select the homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages.first(), homepage)

    def test_not_page(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.not_page(homepage)

        # Should select everything except for the homepage
        self.assertEqual(pages.count(), Page.objects.all().count() - 1)
        for page in pages:
            self.assertNotEqual(page, homepage)

    def test_descendant_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.descendant_of(events_index)

        # Check that all pages descend from events index
        for page in pages:
            self.assertTrue(page.get_ancestors().filter(id=events_index.id).exists())

    def test_descendant_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.descendant_of(events_index, inclusive=True)

        # Check that all pages descend from events index, includes event index
        for page in pages:
            self.assertTrue(page == events_index or page.get_ancestors().filter(id=events_index.id).exists())

        # Check that event index was included
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_descendant_of(events_index)

        # Check that no pages descend from events_index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is not inclusive, events index should be in the results
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_descendant_of_inclusive(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_descendant_of(events_index, inclusive=True)

        # Check that all pages descend from homepage but not events index
        for page in pages:
            self.assertFalse(page.get_ancestors().filter(id=events_index.id).exists())

        # As this is inclusive, events index should not be in the results
        self.assertFalse(pages.filter(id=events_index.id).exists())

    def test_child_of(self):
        homepage = Page.objects.get(url_path='/home/')
        pages = Page.objects.child_of(homepage)

        # Check that all pages are children of homepage
        for page in pages:
            self.assertEqual(page.get_parent(), homepage)

    def test_not_child_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_child_of(events_index)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

    def test_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.ancestor_of(events_index)

        self.assertEqual(pages.count(), 2)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)

    def test_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.ancestor_of(events_index, inclusive=True)

        self.assertEqual(pages.count(), 3)
        self.assertEqual(pages[0], root_page)
        self.assertEqual(pages[1], homepage)
        self.assertEqual(pages[2], events_index)

    def test_not_ancestor_of(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_ancestor_of(events_index)

        # Test that none of the ancestors are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_ancestor_of_inclusive(self):
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_ancestor_of(events_index, inclusive=True)

        # Test that none of the ancestors or the events_index are in pages
        for page in pages:
            self.assertNotEqual(page, root_page)
            self.assertNotEqual(page, homepage)
            self.assertNotEqual(page, events_index)

    def test_parent_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.parent_of(events_index)

        # Pages must only contain homepage
        self.assertEqual(pages.count(), 1)
        self.assertEqual(pages[0], homepage)

    def test_not_parent_of(self):
        homepage = Page.objects.get(url_path='/home/')
        events_index = Page.objects.get(url_path='/home/events/')
        pages = Page.objects.not_parent_of(events_index)

        # Pages must not contain homepage
        for page in pages:
            self.assertNotEqual(page, homepage)

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_sibling_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

    def test_sibling_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.sibling_of(event, inclusive=True)

        # Check that all pages are children of events_index
        for page in pages:
            self.assertEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_not_sibling_of(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event)

        # Check that all pages are not children of events_index
        for page in pages:
            if page != event:
                self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is included
        self.assertTrue(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_not_sibling_of_inclusive(self):
        events_index = Page.objects.get(url_path='/home/events/')
        event = Page.objects.get(url_path='/home/events/christmas/')
        pages = Page.objects.not_sibling_of(event, inclusive=True)

        # Check that all pages are not children of events_index
        for page in pages:
            self.assertNotEqual(page.get_parent(), events_index)

        # Check that the event is not included
        self.assertFalse(pages.filter(id=event.id).exists())

        # Test that events index is in pages
        self.assertTrue(pages.filter(id=events_index.id).exists())

    def test_type(self):
        pages = Page.objects.type(EventPage)

        # Check that all objects are EventPages
        for page in pages:
            self.assertIsInstance(page.specific, EventPage)

        # Check that "someone elses event" is in the results
        event = Page.objects.get(url_path='/home/events/someone-elses-event/')
        self.assertTrue(pages.filter(id=event.id).exists())

    def test_not_type(self):
        pages = Page.objects.not_type(EventPage)

        # Check that no objects are EventPages
        for page in pages:
            self.assertNotIsInstance(page.specific, EventPage)

        # Check that the homepage is in the results
        homepage = Page.objects.get(url_path='/home/')
        self.assertTrue(pages.filter(id=homepage.id).exists())


class TestMovePage(TestCase):
    fixtures = ['test.json']

    def test_move_page(self):
        about_us_page = SimplePage.objects.get(url_path='/home/about-us/')
        events_index = EventIndex.objects.get(url_path='/home/events/')

        events_index.move(about_us_page, pos='last-child')

        # re-fetch events index to confirm that db fields have been updated
        events_index = EventIndex.objects.get(id=events_index.id)
        self.assertEqual(events_index.url_path, '/home/about-us/events/')
        self.assertEqual(events_index.depth, 4)
        self.assertEqual(events_index.get_parent().id, about_us_page.id)

        # children of events_index should also have been updated
        christmas = events_index.get_children().get(slug='christmas')
        self.assertEqual(christmas.depth, 5)
        self.assertEqual(christmas.url_path, '/home/about-us/events/christmas/')


class TestIssue7(TestCase):
    """
    This tests for an issue where if a site root page was moved, all the page 
    urls in that site would change to None.

    The issue was caused by the 'wagtail_site_root_paths' cache variable not being
    cleared when a site root page was moved. Which left all the child pages
    thinking that they are no longer in the site and return None as their url.

    Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
    Discussion: https://github.com/torchbox/wagtail/issues/7
    """

    fixtures = ['test.json']

    def test_issue7(self):
        # Get homepage, root page and site
        root_page = Page.objects.get(id=1)
        homepage = Page.objects.get(url_path='/home/')
        default_site = Site.objects.get(is_default_site=True)

        # Create a new homepage under current homepage
        new_homepage = SimplePage(title="New Homepage", slug="new-homepage")
        homepage.add_child(instance=new_homepage)

        # Set new homepage as the site root page
        default_site.root_page = new_homepage
        default_site.save()

        # Warm up the cache by getting the url
        _ = homepage.url

        # Move new homepage to root
        new_homepage.move(root_page, pos='last-child')

        # Get fresh instance of new_homepage
        new_homepage = Page.objects.get(id=new_homepage.id)

        # Check url
        self.assertEqual(new_homepage.url, '/')


class TestIssue157(TestCase):
    """
    This tests for an issue where if a site root pages slug was changed, all the page 
    urls in that site would change to None.

    The issue was caused by the 'wagtail_site_root_paths' cache variable not being
    cleared when a site root page was changed. Which left all the child pages
    thinking that they are no longer in the site and return None as their url.

    Fix: d6cce69a397d08d5ee81a8cbc1977ab2c9db2682
    Discussion: https://github.com/torchbox/wagtail/issues/157
    """

    fixtures = ['test.json']

    def test_issue157(self):
        # Get homepage
        homepage = Page.objects.get(url_path='/home/')

        # Warm up the cache by getting the url
        _ = homepage.url

        # Change homepage title and slug
        homepage.title = "New home"
        homepage.slug = "new-home"
        homepage.save()

        # Get fresh instance of homepage
        homepage = Page.objects.get(id=homepage.id)

        # Check url
        self.assertEqual(homepage.url, '/')
