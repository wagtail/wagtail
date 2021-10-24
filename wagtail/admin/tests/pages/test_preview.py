import datetime

from functools import wraps
from unittest import mock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.edit_handlers import FieldPanel, ObjectList, TabbedInterface
from wagtail.admin.views.pages.preview import PreviewOnEdit
from wagtail.core.models import Page
from wagtail.tests.testapp.models import EventCategory, EventPage, SimplePage, StreamPage
from wagtail.tests.utils import WagtailTestUtils


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


def clear_edit_handler(page_cls):
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Clear any old EditHandlers generated
            page_cls.get_edit_handler.cache_clear()
            try:
                fn(*args, **kwargs)
            finally:
                # Clear the bad EditHandler generated just now
                page_cls.get_edit_handler.cache_clear()
        return decorated
    return decorator


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
            'comments-TOTAL_FORMS': 0,
            'comments-INITIAL_FORMS': 0,
            'comments-MIN_NUM_FORMS': 0,
            'comments-MAX_NUM_FORMS': 1000,
        }

    def test_preview_on_create_with_m2m_field(self):
        preview_url = reverse('wagtailadmin_pages:preview_on_add',
                              args=('tests', 'eventpage', self.home_page.id))
        response = self.client.post(preview_url, self.post_data)

        # Check the JSON response
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {'is_valid': True})

        # Check the user can refresh the preview
        preview_session_key = 'wagtail-preview-tests-eventpage-{}'.format(self.home_page.id)
        self.assertTrue(preview_session_key in self.client.session)

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

        # Check the user can refresh the preview
        preview_session_key = 'wagtail-preview-{}'.format(self.event_page.id)
        self.assertTrue(preview_session_key in self.client.session)

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

    @clear_edit_handler(EventPage)
    def test_preview_with_custom_edit_handler(self):
        """
        The test is based on TestPreview.test_preview_on_create_with_m2m_field, except that the "categories"
        FieldPanel is only visible to superusers. Non-superusers should not be able to set "categories" for
        the preview.
        """

        class SuperuserEventCategoriesObjectList(ObjectList):
            def on_request_bound(self):
                new_children = []
                for child in self.children:
                    # skip the "categories" FieldPanel for non-superusers
                    if isinstance(child, FieldPanel) and child.field_name == "categories" and not self.request.user.is_superuser:
                        continue

                    new_child = child.bind_to(
                        model=self.model,
                        instance=self.instance,
                        request=self.request,
                        form=self.form,
                    )
                    new_children.append(new_child)
                self.children = new_children

        new_tabbed_interface = TabbedInterface([
            SuperuserEventCategoriesObjectList(EventPage.content_panels),
            ObjectList(EventPage.promote_panels),
        ])

        with mock.patch.object(EventPage, 'edit_handler', new=new_tabbed_interface, create=True):
            # Non-superusers should not see categories panel, so even though "post_data" contains "categories",
            # it should not be considered for the preview request.
            self.login(username='siteeditor', password='password')

            preview_url = reverse('wagtailadmin_pages:preview_on_add',
                                  args=('tests', 'eventpage', self.home_page.id))
            response = self.client.post(preview_url, self.post_data)

            # Check the JSON response
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(response.content.decode(), {'is_valid': True})

            # Check the user can refresh the preview
            preview_session_key = 'wagtail-preview-tests-eventpage-{}'.format(self.home_page.id)
            self.assertTrue(preview_session_key in self.client.session)

            response = self.client.get(preview_url)

            # Check the HTML response
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'tests/event_page.html')
            self.assertContains(response, "Beach party")
            self.assertNotContains(response, "<li>Parties</li>")
            self.assertNotContains(response, "<li>Holidays</li>")

            # Since superusers see the "categories" panel, the posted data should be used for the preview.
            self.login(username='superuser', password='password')
            response = self.client.post(preview_url, self.post_data)

            # Check the JSON response
            self.assertEqual(response.status_code, 200)
            self.assertJSONEqual(response.content.decode(), {'is_valid': True})

            # Check the user can refresh the preview
            preview_session_key = 'wagtail-preview-tests-eventpage-{}'.format(self.home_page.id)
            self.assertTrue(preview_session_key in self.client.session)

            response = self.client.get(preview_url)

            # Check the HTML response
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'tests/event_page.html')
            self.assertContains(response, "Beach party")
            self.assertContains(response, "<li>Parties</li>")
            self.assertContains(response, "<li>Holidays</li>")


class TestDisablePreviewButton(TestCase, WagtailTestUtils):
    """
    Test that preview button can be disabled by setting preview_modes to an empty list
    """
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Login
        self.user = self.login()

    def test_disable_preview_on_create(self):
        # preview button is available by default
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'simplepage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)

        preview_url = reverse('wagtailadmin_pages:preview_on_add', args=('tests', 'simplepage', self.root_page.id))
        self.assertContains(response, '<li class="preview">')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        # StreamPage has preview_modes = []
        response = self.client.get(reverse('wagtailadmin_pages:add', args=('tests', 'streampage', self.root_page.id)))
        self.assertEqual(response.status_code, 200)

        preview_url = reverse('wagtailadmin_pages:preview_on_add', args=('tests', 'streampage', self.root_page.id))
        self.assertNotContains(response, '<li class="preview">')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_edit(self):
        simple_page = SimplePage(title='simple page', content="hello")
        self.root_page.add_child(instance=simple_page)

        # preview button is available by default
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(simple_page.id, )))
        self.assertEqual(response.status_code, 200)

        preview_url = reverse('wagtailadmin_pages:preview_on_edit', args=(simple_page.id, ))
        self.assertContains(response, '<li class="preview">')
        self.assertContains(response, 'data-action="%s"' % preview_url)

        stream_page = StreamPage(title='stream page', body=[('text', 'hello')])
        self.root_page.add_child(instance=stream_page)

        # StreamPage has preview_modes = []
        response = self.client.get(reverse('wagtailadmin_pages:edit', args=(stream_page.id, )))
        self.assertEqual(response.status_code, 200)

        preview_url = reverse('wagtailadmin_pages:preview_on_edit', args=(stream_page.id, ))
        self.assertNotContains(response, '<li class="preview">')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)

    def test_disable_preview_on_revisions_list(self):
        simple_page = SimplePage(title='simple page', content="hello")
        self.root_page.add_child(instance=simple_page)
        simple_page.save_revision()

        # check preview shows up by default
        response = self.client.get(reverse('wagtailadmin_pages:revisions_index', args=(simple_page.id,)))
        preview_url = reverse('wagtailadmin_pages:revisions_view', args=(simple_page.id, simple_page.get_latest_revision().id))
        self.assertContains(response, 'Preview')
        self.assertContains(response, preview_url)

        stream_page = StreamPage(title='stream page', body=[('text', 'hello')])
        self.root_page.add_child(instance=stream_page)
        latest_revision = stream_page.save_revision()

        # StreamPage has preview_modes = []
        response = self.client.get(reverse('wagtailadmin_pages:revisions_index', args=(stream_page.id,)))
        preview_url = reverse('wagtailadmin_pages:revisions_view', args=(stream_page.id, latest_revision.id))
        self.assertNotContains(response, 'Preview')
        self.assertNotContains(response, preview_url)

    def disable_preview_in_moderation_list(self):
        stream_page = StreamPage(title='stream page', body=[('text', 'hello')])
        self.root_page.add_child(instance=stream_page)
        latest_revision = stream_page.save_revision(user=self.user, submitted_for_moderation=True)

        response = self.client.get(reverse('wagtailadmin_home'))
        preview_url = reverse('wagtailadmin_pages:preview_for_moderation', args=(latest_revision.id,))
        self.assertNotContains(response, '<li class="preview">')
        self.assertNotContains(response, 'data-action="%s"' % preview_url)
