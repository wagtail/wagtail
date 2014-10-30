from datetime import timedelta

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.paginator import Paginator
from django.utils import timezone

from wagtail.tests.models import (
    SimplePage, EventPage, EventPageCarouselItem,
    StandardIndex, StandardChild,
    BusinessIndex, BusinessChild, BusinessSubIndex,
    TaggedPage, Advert, AdvertPlacement)
from wagtail.tests.utils import unittest, WagtailTestUtils
from wagtail.wagtailcore.models import Page, PageRevision
from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.wagtailusers.models import UserProfile


def submittable_timestamp(timestamp):
    """
    Helper function to translate a possibly-timezone-aware datetime into the format used in the
    go_live_at / expire_at form fields - "YYYY-MM-DD hh:mm", with no timezone indicator.
    This will be interpreted as being in the server's timezone (settings.TIME_ZONE), so we
    need to pass it through timezone.localtime to ensure that the client and server are in
    agreement about what the timestamp means.
    """
    return str(timezone.localtime(timestamp)).split('.')[0]


class TestPageExplorer(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
        )
        self.root_page.add_child(instance=self.child_page)

        # Login
        self.login()

    def test_explore(self):
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(self.root_page, response.context['parent_page'])
        self.assertTrue(response.context['pages'].paginator.object_list.filter(id=self.child_page.id).exists())

    def test_explore_root(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(Page.objects.get(id=1), response.context['parent_page'])
        self.assertTrue(response.context['pages'].paginator.object_list.filter(id=self.root_page.id).exists())

    def test_ordering(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'), {'ordering': 'content_type'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], 'content_type')

    def test_invalid_ordering(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'), {'ordering': 'invalid_order'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], '-latest_revision_created_at')

    def test_reordering(self):
        response = self.client.get(reverse('wagtailadmin_explore_root'), {'ordering': 'ord'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/index.html')
        self.assertEqual(response.context['ordering'], 'ord')

        # Pages must not be paginated
        self.assertNotIsInstance(response.context['pages'], Paginator)

    def make_pages(self):
        for i in range(150):
            self.root_page.add_child(instance=SimplePage(
                title="Page " + str(i),
                slug="page-" + str(i),
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


class TestPageCreation(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_add_subpage(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.root_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_add_subpage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get add subpage page
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.root_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_add_subpage_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(100000, )))
        self.assertEqual(response.status_code, 404)

    def test_create_simplepage(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)

    def test_create_simplepage_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get page
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_create_simplepage_post(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(page.id, )))
       
        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)

    def test_create_simplepage_scheduled(self):
        go_live_at = timezone.now() + timedelta(days=1)
        expire_at = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

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
            'go_live_at': submittable_timestamp(timezone.now() + timedelta(days=2)),
            'expire_at': submittable_timestamp(timezone.now() + timedelta(days=1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'go_live_at', "Go live date/time must be before expiry date/time")
        self.assertFormError(response, 'form', 'expire_at', "Go live date/time must be before expiry date/time")

    def test_create_simplepage_scheduled_expire_in_the_past(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'expire_at': submittable_timestamp(timezone.now() + timedelta(days=-1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'expire_at', "Expiry date/time must be in the future")

    def test_create_simplepage_post_publish(self):
        # Connect a mock signal handler to page_published signal
        signal_fired = [False]
        signal_page = [None]
        def page_published_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance
        page_published.connect(page_published_handler)

        # Post
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertTrue(page.live)

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_create_simplepage_post_publish_scheduled(self):
        go_live_at = timezone.now() + timedelta(days=1)
        expire_at = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

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
        self.assertTrue(page.status_string, "scheduled")

    def test_create_simplepage_post_submit(self):
        # Create a moderator user for testing email
        moderator = get_user_model().objects.create_superuser('moderator', 'moderator@email.com', 'password')

        # Submit
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='hello-world').specific

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))
       
        self.assertEqual(page.title, post_data['title'])
        self.assertIsInstance(page, SimplePage)
        self.assertFalse(page.live)

        # The latest revision for the page should now be in moderation
        self.assertTrue(page.get_latest_revision().submitted_for_moderation)

        # Check that the moderator got an email
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['moderator@email.com'])
        self.assertEqual(mail.outbox[0].subject, 'The page "New page!" has been submitted for moderation')

    def test_create_simplepage_post_existing_slug(self):
        # This tests the existing slug checking on page save

        # Create a page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(instance=self.child_page)

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

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'slug', "This slug is already in use")

    def test_create_nonexistantparent(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'simplepage', 100000)))
        self.assertEqual(response.status_code, 404)

    def test_create_nonpagetype(self):
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('wagtailimages', 'image', self.root_page.id)))
        self.assertEqual(response.status_code, 404)

    def test_preview_on_create(self):
        post_data = {
            'title': "New page!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages_preview_on_create', args=('tests', 'simplepage', self.root_page.id)), post_data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "New page!")

        # Check that the treebeard attributes were set correctly on the page object
        self.assertEqual(response.context['self'].depth, self.root_page.depth + 1)
        self.assertTrue(response.context['self'].path.startswith(self.root_page.path))
        self.assertEqual(response.context['self'].get_parent(), self.root_page)


class TestPageEdit(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.child_page.live = True
        self.root_page.add_child(instance=self.child_page)
        self.child_page.save_revision()

        # Add event page (to test edit handlers)
        self.event_page = EventPage()
        self.event_page.title = "Event page"
        self.event_page.slug = "event-page"
        self.root_page.add_child(instance=self.event_page)

        # Login
        self.user = self.login()

    def test_page_edit(self):
        # Tests that the edit page loads
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_edit_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get edit page
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_edit_post(self):
        # Tests simple editing
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)
    
        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )))

        # The page should have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertTrue(child_page_new.has_unpublished_changes)

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
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)
    
        # Shouldn't be redirected
        self.assertContains(response, "The page could not be saved as it is locked")

        # The page shouldn't have "has_unpublished_changes" flag set
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertFalse(child_page_new.has_unpublished_changes)

    def test_edit_post_scheduled(self):
        # put go_live_at and expire_at several days away from the current date, to avoid
        # false matches in content_json__contains tests
        go_live_at = timezone.now() + timedelta(days=10)
        expire_at = timezone.now() + timedelta(days=20)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page will still be live
        self.assertTrue(child_page_new.live)

        # A revision with approved_go_live_at should not exist
        self.assertFalse(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists())

        # But a revision with go_live_at and expire_at in their content json *should* exist
        self.assertTrue(PageRevision.objects.filter(page=child_page_new, content_json__contains=str(go_live_at.date())).exists())
        self.assertTrue(PageRevision.objects.filter(page=child_page_new, content_json__contains=str(expire_at.date())).exists())

    def test_edit_scheduled_go_live_before_expiry(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'go_live_at': submittable_timestamp(timezone.now() + timedelta(days=2)),
            'expire_at': submittable_timestamp(timezone.now() + timedelta(days=1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'go_live_at', "Go live date/time must be before expiry date/time")
        self.assertFormError(response, 'form', 'expire_at', "Go live date/time must be before expiry date/time")

    def test_edit_scheduled_expire_in_the_past(self):
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'expire_at': submittable_timestamp(timezone.now() + timedelta(days=-1)),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'expire_at', "Expiry date/time must be in the future")

    def test_page_edit_post_publish(self):
        # Connect a mock signal handler to page_published signal
        signal_fired = [False]
        signal_page = [None]
        def page_published_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance
        page_published.connect(page_published_handler)

        # Set has_unpublished_changes=True on the existing record to confirm that the publish action
        # is resetting it (and not just leaving it alone)
        self.child_page.has_unpublished_changes = True
        self.child_page.save()

        # Tests publish from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)
    
        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was edited
        child_page_new = SimplePage.objects.get(id=self.child_page.id)
        self.assertEqual(child_page_new.title, post_data['title'])

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], child_page_new)
        self.assertEqual(signal_page[0], signal_page[0].specific)

        # The page shouldn't have "has_unpublished_changes" flag set
        self.assertFalse(child_page_new.has_unpublished_changes)

    def test_edit_post_publish_scheduled(self):
        go_live_at = timezone.now() + timedelta(days=1)
        expire_at = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live anymore
        self.assertFalse(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists())

        # The page SHOULD have the "has_unpublished_changes" flag set, because the changes are not visible as a live page yet
        self.assertTrue(child_page_new.has_unpublished_changes, "A page scheduled for future publishing should have has_unpublished_changes=True")

    def test_edit_post_publish_now_an_already_scheduled(self):
        # First let's publish a page with a go_live_at in the future
        go_live_at = timezone.now() + timedelta(days=1)
        expire_at = timezone.now() + timedelta(days=2)
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': submittable_timestamp(go_live_at),
            'expire_at': submittable_timestamp(expire_at),
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should not be live anymore
        self.assertFalse(child_page_new.live)

        # Instead a revision with approved_go_live_at should now exist
        self.assertTrue(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists())

        # Now, let's edit it and publish it right now
        go_live_at = timezone.now()
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-publish': "Publish",
            'go_live_at': "",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

        # Should be redirected to edit page
        self.assertEqual(response.status_code, 302)

        child_page_new = SimplePage.objects.get(id=self.child_page.id)

        # The page should be live now
        self.assertTrue(child_page_new.live)

        # And a revision with approved_go_live_at should not exist
        self.assertFalse(PageRevision.objects.filter(page=child_page_new).exclude(approved_go_live_at__isnull=True).exists())

    def test_page_edit_post_submit(self):
        # Create a moderator user for testing email
        moderator = get_user_model().objects.create_superuser('moderator', 'moderator@email.com', 'password')

        # Tests submitting from edit page
        post_data = {
            'title': "I've been edited!",
            'content': "Some content",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)
    
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
        self.assertEqual(mail.outbox[0].subject, 'The page "Hello world!" has been submitted for moderation') # Note: should this be "I've been edited!"?

    def test_page_edit_post_existing_slug(self):
        # This tests the existing slug checking on page edit

        # Create a page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world 2"
        self.child_page.slug = "hello-world2"
        self.root_page.add_child(instance=self.child_page)

        # Attempt to change the slug to one thats already in use
        post_data = {
            'title': "Hello world 2",
            'slug': 'hello-world',
            'action-submit': "Submit",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), post_data)

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
        response = self.client.post(reverse('wagtailadmin_pages_preview_on_edit', args=(self.child_page.id, )), post_data)

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tests/simple_page.html')
        self.assertContains(response, "I&#39;ve been edited!")


class TestPageEditReordering(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add event page
        self.event_page = EventPage()
        self.event_page.title = "Event page"
        self.event_page.slug = "event-page"
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
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )))

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
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )), post_data)

        # Should be redirected back to same page
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )))

        # Check order
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )))

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])

    def test_reorder_with_validation_error(self):
        post_data = {
            'title': "", # Validation error
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
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.event_page.id, )), post_data)

        self.assertEqual(response.status_code, 200)
        self.check_order(response, ['abcdefg', '1234567', '7654321'])


class TestPageDelete(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage()
        self.child_page.title = "Hello world!"
        self.child_page.slug = "hello-world"
        self.root_page.add_child(instance=self.child_page)

        # Login
        self.user = self.login()

    def test_page_delete(self):
        response = self.client.get(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_delete_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get delete page
        response = self.client.get(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_delete_post(self):
        # Connect a mock signal handler to page_unpublished signal
        signal_fired = [False]
        signal_page = [None]
        def page_unpublished_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance
        page_unpublished.connect(page_unpublished_handler)

        # Post
        post_data = {'hello': 'world'} # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], self.child_page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_page_delete_notlive_post(self):
        # Same as above, but this makes sure the page_unpublished signal is not fired
        # when if the page is not live when it is deleted

        # Unpublish the page
        self.child_page.live = False
        self.child_page.save()

        # Connect a mock signal handler to page_unpublished signal
        signal_fired = [False]
        def page_unpublished_handler(sender, instance, **kwargs):
            signal_fired[0] = True
        page_unpublished.connect(page_unpublished_handler)

        # Post
        post_data = {'hello': 'world'} # For some reason, this test doesn't work without a bit of POST data
        response = self.client.post(reverse('wagtailadmin_pages_delete', args=(self.child_page.id, )), post_data)

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is gone
        self.assertEqual(Page.objects.filter(path__startswith=self.root_page.path, slug='hello-world').count(), 0)

        # Check that the page_unpublished signal was not fired
        self.assertFalse(signal_fired[0])


class TestPageSearch(TestCase, WagtailTestUtils):
    def setUp(self):
        # Login
        self.login()

    def get(self, params=None, **extra):
        return self.client.get(reverse('wagtailadmin_pages_search'), params or {}, **extra)

    def test_view(self):
        response = self.get()
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/search.html')
        self.assertEqual(response.context['query_string'], "Hello")

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


class TestPageMove(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create two sections
        self.section_a = SimplePage()
        self.section_a.title = "Section A"
        self.section_a.slug = "section-a"
        self.root_page.add_child(instance=self.section_a)

        self.section_b = SimplePage()
        self.section_b.title = "Section B"
        self.section_b.slug = "section-b"
        self.root_page.add_child(instance=self.section_b)

        # Add test page into section A
        self.test_page = SimplePage()
        self.test_page.title = "Hello world!"
        self.test_page.slug = "hello-world"
        self.section_a.add_child(instance=self.test_page)

        # Login
        self.user = self.login()

    def test_page_move(self):
        response = self.client.get(reverse('wagtailadmin_pages_move', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)

    def test_page_move_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get move page
        response = self.client.get(reverse('wagtailadmin_pages_move', args=(self.test_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_move_confirm(self):
        response = self.client.get(reverse('wagtailadmin_pages_move_confirm', args=(self.test_page.id, self.section_b.id)))
        self.assertEqual(response.status_code, 200)

    def test_page_set_page_position(self):
        response = self.client.get(reverse('wagtailadmin_pages_set_page_position', args=(self.test_page.id, )))
        self.assertEqual(response.status_code, 200)


class TestPageCopy(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page
        self.test_page = self.root_page.add_child(instance=SimplePage(
            title="Hello world!",
            slug='hello-world',
            live=True,
            has_unpublished_changes=False,
        ))

        # Create a couple of child pages
        self.test_child_page = self.test_page.add_child(instance=SimplePage(
            title="Child page",
            slug='child-page',
            live=True,
            has_unpublished_changes=True,
        ))

        self.test_unpublished_child_page = self.test_page.add_child(instance=SimplePage(
            title="Unpublished Child page",
            slug='unpublished-child-page',
            live=False,
            has_unpublished_changes=True,
        ))

        # Login
        self.user = self.login()

    def test_page_copy(self):
        response = self.client.get(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/copy.html')

        # Make sure all fields are in the form
        self.assertContains(response, "New title")
        self.assertContains(response, "New slug")
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
        response = self.client.get(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_page_copy_post(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'copy_subpages': False,
            'publish_copies': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

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

    def test_page_copy_post_copy_subpages(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'copy_subpages': True,
            'publish_copies': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

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

    def test_page_copy_post_copy_subpages_publish_copies(self):
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world-2',
            'copy_subpages': True,
            'publish_copies': True,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

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

    def test_page_copy_post_existing_slug(self):
        # This tests the existing slug checking on page copy

        # Attempt to copy the page but forget to change the slug
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello-world',
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'new_slug', "This slug is already in use")

    def test_page_copy_post_invalid_slug(self):
        # Attempt to copy the page but set an invalid slug string
        post_data = {
            'new_title': "Hello world 2",
            'new_slug': 'hello world!',
            'copy_subpages': False,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

        # Should not be redirected (as the save should fail)
        self.assertEqual(response.status_code, 200)

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'new_slug', "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.")

    def test_page_copy_no_publish_permission(self):
        # Turn user into an editor who can add pages but not publish them
        self.user.is_superuser = False
        self.user.groups.add(
            Group.objects.get(name="Editors"),
        )
        self.user.save()

        # Get copy page
        response = self.client.get(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )))

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
            'copy_subpages': True,
            'publish_copies': True,
        }
        response = self.client.post(reverse('wagtailadmin_pages_copy', args=(self.test_page.id, )), post_data)

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


class TestPageUnpublish(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

        # Create a page to unpublish
        self.root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug='hello-world',
            live=True,
        )
        self.root_page.add_child(instance=self.page)

    def test_unpublish_view(self):
        """
        This tests that the unpublish view responds with an unpublish confirm page
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages_unpublish', args=(self.page.id, )))

        # Check that the user recieved an unpublish confirm page
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/pages/confirm_unpublish.html')

    def test_unpublish_view_invalid_page_id(self):
        """
        This tests that the unpublish view returns an error if the page id is invalid
        """
        # Get unpublish page
        response = self.client.get(reverse('wagtailadmin_pages_unpublish', args=(12345, )))

        # Check that the user recieved a 404 response
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
        response = self.client.get(reverse('wagtailadmin_pages_unpublish', args=(self.page.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_unpublish_view_post(self):
        """
        This posts to the unpublish view and checks that the page was unpublished
        """
        # Connect a mock signal handler to page_unpublished signal
        signal_fired = [False]
        signal_page = [None]
        def page_unpublished_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance
        page_unpublished.connect(page_unpublished_handler)

        # Post to the unpublish page
        response = self.client.post(reverse('wagtailadmin_pages_unpublish', args=(self.page.id, )))

        # Should be redirected to explorer page
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page was unpublished
        self.assertFalse(SimplePage.objects.get(id=self.page.id).live)

        # Check that the page_unpublished signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], self.page)
        self.assertEqual(signal_page[0], signal_page[0].specific)


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
        signal_fired = [False]
        signal_page = [None]
        def page_published_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance
        page_published.connect(page_published_handler)

        # Post
        response = self.client.post(reverse('wagtailadmin_pages_approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page should now have no unpublished changes
        self.assertFalse(page.has_unpublished_changes, "Approving moderation failed to set has_unpublished_changes=False")

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], self.page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_approve_moderation_when_later_revision_exists(self):
        self.page.title = "Goodbye world!"
        self.page.save_revision(user=self.submitter, submitted_for_moderation=False)

        response = self.client.post(reverse('wagtailadmin_pages_approve_moderation', args=(self.revision.id, )))

        # Check that the user was redirected to the dashboard
        self.assertRedirects(response, reverse('wagtailadmin_home'))

        page = Page.objects.get(id=self.page.id)
        # Page must be live
        self.assertTrue(page.live, "Approving moderation failed to set live=True")
        # Page content should be the submitted version, not the published one
        self.assertEqual(page.title, "Hello world!")
        # Page should still have unpublished changes
        self.assertTrue(page.has_unpublished_changes, "has_unpublished_changes incorrectly cleared on approve_moderation when a later revision exists")

    def test_approve_moderation_view_bad_revision_id(self):
        """
        This tests that the approve moderation view handles invalid revision ids correctly
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages_approve_moderation', args=(12345, )))

        # Check that the user recieved a 404 response
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
        response = self.client.post(reverse('wagtailadmin_pages_approve_moderation', args=(self.revision.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_reject_moderation_view(self):
        """
        This posts to the reject moderation view and checks that the page was rejected
        """
        # Post
        response = self.client.post(reverse('wagtailadmin_pages_reject_moderation', args=(self.revision.id, )))

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
        response = self.client.post(reverse('wagtailadmin_pages_reject_moderation', args=(12345, )))

        # Check that the user recieved a 404 response
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
        response = self.client.post(reverse('wagtailadmin_pages_reject_moderation', args=(self.revision.id, )))

        # Check that the user recieved a 403 response
        self.assertEqual(response.status_code, 403)

    def test_preview_for_moderation(self):
        response = self.client.get(reverse('wagtailadmin_pages_preview_for_moderation', args=(self.revision.id, )))

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
        response = self.client.get(reverse('wagtailadmin_pages_type_use', args=('tests', 'eventpage')))

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
        add_subpage_url = reverse('wagtailadmin_pages_add_subpage', args=(self.standard_index.id, ))

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
        add_subpage_url = reverse('wagtailadmin_pages_add_subpage', args=(self.business_index.id, ))

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
        add_subpage_url = reverse('wagtailadmin_pages_add_subpage', args=(self.business_child.id, ))

        # explorer should not contain a link to 'add child page', as this page doesn't accept subpages
        response = self.client.get(reverse('wagtailadmin_explore', args=(self.business_child.id, )))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, add_subpage_url)

        # this also means that fetching add_subpage is blocked at the permission-check level
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.business_child.id, )))
        self.assertEqual(response.status_code, 403)

    def test_cannot_add_invalid_subpage_type(self):
        # cannot add StandardChild as a child of BusinessIndex, as StandardChild is not present in subpage_types
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'standardchild', self.business_index.id)))
        self.assertEqual(response.status_code, 403)

        # likewise for BusinessChild which has an empty subpage_types list
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'standardchild', self.business_child.id)))
        self.assertEqual(response.status_code, 403)

        # cannot add BusinessChild to StandardIndex, as BusinessChild restricts is parent page types
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'businesschild', self.standard_index.id)))
        self.assertEqual(response.status_code, 403)

        # but we can add a BusinessChild to BusinessIndex
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'businesschild', self.business_index.id)))
        self.assertEqual(response.status_code, 200)

    def test_not_prompted_for_page_type_when_only_one_choice(self):
        response = self.client.get(reverse('wagtailadmin_pages_add_subpage', args=(self.business_subindex.id, )))
        # BusinessChild is the only valid subpage type of BusinessSubIndex, so redirect straight there
        self.assertRedirects(response, reverse('wagtailadmin_pages_create', args=('tests', 'businesschild', self.business_subindex.id)))


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
        return self.client.post(reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )), self.post_data)

    def silent_submit(self):
        """
        Sets up the child_page as needing moderation, without making a request
        """
        self.child_page.save_revision(user=self.submitter, submitted_for_moderation=True)
        self.revision = self.child_page.get_latest_revision()

    def approve(self):
        return self.client.post(reverse('wagtailadmin_pages_approve_moderation', args=(self.revision.id, )))

    def reject(self):
        return self.client.post(reverse('wagtailadmin_pages_reject_moderation', args=(self.revision.id, )))

    def test_vanilla_profile(self):
        # Check that the vanilla profile has rejected notifications on
        self.assertEqual(self.submitter_profile.rejected_notifications, True)

        # Check that the vanilla profile has approved notifications on
        self.assertEqual(self.submitter_profile.approved_notifications, True)

    def test_submit_notifications_sent(self):
        # Submit
        self.submit()

        # Check that both the moderators got an email, and no others
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.moderator.email, mail.outbox[0].to)
        self.assertIn(self.moderator2.email, mail.outbox[0].to)
        self.assertEqual(len(mail.outbox[0].to), 2)

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

        # Submitter must recieve an approved email
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

        # Submitter must recieve a rejected email
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
            live=False,
        )
        self.root_page.add_child(instance=self.child_page)

    def test_lock_post(self):
        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_get(self):
        response = self.client.get(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_already_locked(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_with_good_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages_edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )))

        # Check that the page is locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_bad_redirect(self):
        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )), {
            'next': 'http://www.google.co.uk'
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is locked
        self.assertTrue(page.objects.get(id=self.child_page.id).locked)

    def test_lock_post_bad_page(self):
        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(9999, )))

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

        response = self.client.post(reverse('wagtailadmin_pages_lock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_get(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.get(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

        # Check that the page is still locked
        self.assertTrue(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_already_unlocked(self):
        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Check that the page is still unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_good_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )), {
            'next': reverse('wagtailadmin_pages_edit', args=(self.child_page.id, ))
        })

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(self.child_page.id, )))

        # Check that the page is unlocked
        self.assertFalse(Page.objects.get(id=self.child_page.id).locked)

    def test_unlock_post_with_bad_redirect(self):
        # Lock the page
        self.child_page.locked = True
        self.child_page.save()

        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )), {
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

        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(9999, )))

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

        response = self.client.post(reverse('wagtailadmin_pages_unlock', args=(self.child_page.id, )))

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
            'slug':'tagged-page',
            'tags': "hello, world",
            'action-publish': "Publish",
        }
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.tagged_page.id, )), post_data)

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
        response = self.client.get(reverse('wagtailadmin_pages_create', args=('tests', 'standardindex', self.root_page.id)))
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
        response = self.client.post(reverse('wagtailadmin_pages_create', args=('tests', 'standardindex', self.root_page.id)), post_data)

        # Find the page and check it
        page = Page.objects.get(path__startswith=self.root_page.path, slug='new-index').specific

        # Should be redirected to edit page
        self.assertRedirects(response, reverse('wagtailadmin_pages_edit', args=(page.id, )))

        self.assertEqual(page.advert_placements.count(), 1)
        self.assertEqual(page.advert_placements.first().advert.text, 'test_advert')

    def test_get_edit_form(self):
        response = self.client.get(reverse('wagtailadmin_pages_edit', args=(self.index_page.id, )))
        self.assertEqual(response.status_code, 200)

        # Response should include an advert_placements formset labelled Adverts
        self.assertContains(response, "Adverts")
        self.assertContains(response, "id_advert_placements-TOTAL_FORMS")
        # the formset should be populated with an existing form
        self.assertContains(response, "id_advert_placements-0-advert")
        self.assertContains(response, '<option value="1" selected="selected">test_advert</option>')

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
        response = self.client.post(reverse('wagtailadmin_pages_edit', args=(self.index_page.id, )), post_data)

        # Should be redirected to explorer
        self.assertRedirects(response, reverse('wagtailadmin_explore', args=(self.root_page.id, )))

        # Find the page and check it
        page = Page.objects.get(id=self.index_page.id).specific
        self.assertEqual(page.advert_placements.count(), 2)
        self.assertEqual(page.advert_placements.all()[0].advert.text, 'test_advert')
        self.assertEqual(page.advert_placements.all()[1].advert.text, 'test_advert')
