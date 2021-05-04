from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page, PageLogEntry
from wagtail.tests.utils import WagtailTestUtils


class TestWorkflowHistoryDetail(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.create_test_user()
        self.login(self.user)

        self.christmas_event = Page.objects.get(url_path='/home/events/christmas/')
        self.christmas_event.save_revision()

        workflow = self.christmas_event.get_workflow()
        self.workflow_state = workflow.start(self.christmas_event, self.user)

    def test_get_index(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:workflow_history', args=[self.christmas_event.id])
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, reverse('wagtailadmin_pages:edit', args=[self.christmas_event.id]))
        self.assertContains(response, reverse('wagtailadmin_pages:workflow_history_detail', args=[self.christmas_event.id, self.workflow_state.id]))

    def test_get_index_with_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.get(
            reverse('wagtailadmin_pages:workflow_history', args=[self.christmas_event.id])
        )

        self.assertEqual(response.status_code, 302)

    def test_get_detail(self):
        response = self.client.get(
            reverse('wagtailadmin_pages:workflow_history_detail', args=[self.christmas_event.id, self.workflow_state.id])
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, reverse('wagtailadmin_pages:edit', args=[self.christmas_event.id]))
        self.assertContains(response, reverse('wagtailadmin_pages:workflow_history', args=[self.christmas_event.id]))

    def test_get_detail_with_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.get(
            reverse('wagtailadmin_pages:workflow_history_detail', args=[self.christmas_event.id, self.workflow_state.id])
        )

        self.assertEqual(response.status_code, 302)


class TestFiltering(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()
        self.home_page = Page.objects.get(url_path='/home/')

        self.create_log = PageLogEntry.objects.log_action(self.home_page, 'wagtail.create')
        self.edit_log_1 = PageLogEntry.objects.log_action(self.home_page, 'wagtail.edit')
        self.edit_log_2 = PageLogEntry.objects.log_action(self.home_page, 'wagtail.edit')
        self.edit_log_3 = PageLogEntry.objects.log_action(self.home_page, 'wagtail.edit')

        self.create_comment_log = PageLogEntry.objects.log_action(self.home_page, 'wagtail.comments.create', data={
            'comment': {
                'contentpath': 'title',
                'text': 'Foo',
            }
        })
        self.edit_comment_log = PageLogEntry.objects.log_action(self.home_page, 'wagtail.comments.edit', data={
            'comment': {
                'contentpath': 'title',
                'text': 'Edited',
            }
        })
        self.create_reply_log = PageLogEntry.objects.log_action(self.home_page, 'wagtail.comments.create_reply', data={
            'comment': {
                'contentpath': 'title',
                'text': 'Foo',
            }
        })

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_reports:site_history'), params)
        return self.client.get(reverse('wagtailadmin_pages:workflow_history', args=[self.home_page.id]), params)

    def assert_log_entries(self, response, expected):
        actual = set(response.context['object_list'])
        self.assertSetEqual(actual, set(expected))

    def test_unfiltered(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(response, [
            self.create_log,
            self.edit_log_1,
            self.edit_log_2,
            self.edit_log_3,
            self.create_comment_log,
            self.edit_comment_log,
            self.create_reply_log,
        ])

    def test_filter_by_action(self):
        response = self.get(params={'action': 'wagtail.edit'})
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(response, [
            self.edit_log_1,
            self.edit_log_2,
            self.edit_log_3,
        ])

    def test_hide_commenting_actions(self):
        response = self.get(params={'hide_commenting_actions': 'on'})
        self.assertEqual(response.status_code, 200)
        self.assert_log_entries(response, [
            self.create_log,
            self.edit_log_1,
            self.edit_log_2,
            self.edit_log_3,
        ])
