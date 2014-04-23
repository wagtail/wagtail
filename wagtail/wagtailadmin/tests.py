from datetime import datetime, timedelta
from django.utils import timezone
from django.test import TestCase
import unittest
from wagtail.tests.models import SimplePage, EventPage
from wagtail.tests.utils import login
from wagtail.wagtailcore.models import Page, PageRevision
from django.core.urlresolvers import reverse


class TestHome(TestCase):
    def setUp(self):
        # Login
        login(self.client)

    def test_status_code(self):
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertEqual(response.status_code, 200)


class TestPageExplorer(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_explore(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.root_page, response.context['parent_page'])
        self.assertTrue(response.context['pages'].filter(id=self.child_page.id).exists())


class TestPageSelectTypeLocation(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        login(self.client)

    def test_select_type(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_type'))
        self.assertEqual(response.status_code, 200)

    @unittest.expectedFailure  # For some reason, this returns a 302...
    def test_select_location_testpage(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('tests', 'eventpage')))
        self.assertEqual(response.status_code, 200)

    def test_select_location_nonexistanttype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('notanapp', 'notamodel')))
        self.assertEqual(response.status_code, 404)

    def test_select_location_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_select_location', args=('wagtailimages', 'image')))
        self.assertEqual(response.status_code, 404)


class TestPageCreation(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        login(self.client)

    def test_add_subpage(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_add_subpage_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(100000, )))
        self.assertEqual(response.status_code, 404)

    def test_create_simplepage(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)

    def test_create_simplepage_post(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)

    def test_create_simplepage_scheduled(self):
        go_live_datetime = timezone.now() + timedelta(days=1)
        expiry_datetime = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_datetime': str(go_live_datetime),
            'expiry_datetime': str(expiry_datetime),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check the scheduled times
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEquals(page.go_live_datetime.date(), go_live_datetime.date())
        self.assertEquals(page.expiry_datetime.date(), expiry_datetime.date())
        self.assertEquals(page.expired, False)
        self.assertTrue(page.status_string, "draft")

        # No revisions with approved_go_live_datetime
        self.assertFalse(PageRevision.objects.filter(page=page).exclude(approved_go_live_datetime__isnull=True).exists())

    def test_create_simplepage_scheduled_errored(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_datetime': str(timezone.now() + timedelta(days=2)),
            'expiry_datetime': str(timezone.now() + timedelta(days=1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['edit_handler'].form.errors)

        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'expiry_datetime': str(timezone.now() + timedelta(days=-1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['edit_handler'].form.errors)

    def test_create_simplepage_post_publish(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertTrue(page.live)

    def test_create_simplepage_post_publish_scheduled(self):
        go_live_datetime = timezone.now() + timedelta(days=1)
        expiry_datetime = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_datetime': str(go_live_datetime),
            'expiry_datetime': str(expiry_datetime),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific
        self.assertEquals(page.go_live_datetime.date(), go_live_datetime.date())
        self.assertEquals(page.expiry_datetime.date(), expiry_datetime.date())
        self.assertEquals(page.expired, False)

        # A revision with approved_go_live_datetime should exist now
        self.assertTrue(PageRevision.objects.filter(page=page).exclude(approved_go_live_datetime__isnull=True).exists())
        # But Page won't be live
        self.assertFalse(page.live)
        self.assertTrue(page.status_string, "scheduled")

    def test_create_simplepage_post_existingslug(self):
        # This tests the existing slug checking on page save

        # Create a page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Attempt to create a new one with the same slug
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

    def test_create_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', 100000)))
        self.assertEqual(response.status_code, 404)

    @unittest.expectedFailure  # FIXME: Crashes!
    def test_create_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('wagtailimages', 'image', self.root_page.id)))
        self.assertEqual(response.status_code, 404)


class TestPageEdit(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.child_page.live = True
        self.root_page.add_child(self.child_page)
        self.child_page.save_revision()

        # Add event page (to test edit handlers)
        self.event_page = EventPage()
        self.event_page.title = "Event page"
        self.event_page.slug = "event-page"
        self.root_page.add_child(self.event_page)

        # Login
        login(self.client)

    def test_edit_page(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_edit_post(self):
        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

    def test_edit_post_scheduled(self):
        go_live_datetime = timezone.now() + timedelta(days=1)
        expiry_datetime = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_datetime': str(go_live_datetime),
            'expiry_datetime': str(expiry_datetime),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page will still be live
        self.assertTrue(child_page_new.live)
        # A revision with approved_go_live_datetime should not exist
        self.assertFalse(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_datetime__isnull=True).exists())
        # But a revision with go_live_datetime and expiry_datetime in their content json *should* exist
        self.assertTrue(PageRevision.objects.filter(page=child_page_new, content_json__contains=str(go_live_datetime.date())).exists())
        self.assertTrue(PageRevision.objects.filter(page=child_page_new, content_json__contains=str(expiry_datetime.date())).exists())

    def test_edit_post_publish(self):
        # Tests publish from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the page was edited
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertEqual(child_page_new.title, post_data['title'])

        # The page shouldn't have "has_unpublished_changes" flag set
        self.assertFalse(child_page_new.has_unpublished_changes)

    def test_edit_post_publish_scheduled(self):
        go_live_datetime = timezone.now() + timedelta(days=1)
        expiry_datetime = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_datetime': str(go_live_datetime),
            'expiry_datetime': str(expiry_datetime),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        # The page should not be live anymore
        self.assertFalse(child_page_new.live)
        # Instead a revision with approved_go_live_datetime should not exist
        self.assertTrue(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_datetime__isnull=True).exists())


class TestPageDelete(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(self.child_page)

        # Login
        login(self.client)

    def test_delete(self):
        response = self.client.get(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        post_data = {'hello': 'world'}  # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)


class TestPageSearch(TestCase):
    def setUp(self):
        # Login
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_pages_search'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_root_can_appear_in_search_results(self):
        response = self.client.get('/admin/pages/search/?q=roo')
        self.assertEqual(response.status_code, 200)
        # 'pages' list in the response should contain root
        results = response.context['pages']
        self.assertTrue(any([r.slug == 'root' for r in results]))


class TestPageMove(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create two sections
        self.section_a = SimplePage()
        self.section_a.title = "Section A"
        self.section_a.slug = "section-a"
        self.root_page.add_child(self.section_a)

        self.section_b = SimplePage()
        self.section_b.title = "Section B"
        self.section_b.slug = "section-b"
        self.root_page.add_child(self.section_b)

        # Add test page into section A
        self.test_page = SimplePage()
        self.test_page.title = "Hello world!"
        self.test_page.slug = "hello-world"
        self.section_a.add_child(self.test_page)

        # Login
        login(self.client)

    def test_page_move(self):
        response = self.client.get(reverse('wagtailadmin_pages_move', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_move_confirm(self):
        response = self.client.get(reverse('wagtailadmin_pages_move_confirm', args=(self.test_page.id, self.section_b.id)))
        self.assertEqual(response.status_code, 200)

    def test_page_set_page_position(self):
        response = self.client.get(reverse('wagtailadmin_pages_set_page_position', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)


class TestEditorHooks(TestCase):
    def setUp(self):
        self.homepage = Page.objects.get(id=2)
        login(self.client)

    def test_editor_css_and_js_hooks_on_add(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.homepage.id)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')

    def test_editor_css_and_js_hooks_on_edit(self):
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.homepage.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="stylesheet" href="/path/to/my/custom.css">')
        self.assertContains(response, '<script src="/path/to/my/custom.js"></script>')
