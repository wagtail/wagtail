import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from wagtail.admin.views.pages import PreviewOnEdit
from wagtail.core.models import Page
from wagtail.tests.testapp.models import EventCategory
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
