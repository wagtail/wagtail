import datetime

from io import BytesIO

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from wagtail.core.models import Page, PageLogEntry
from wagtail.tests.utils import WagtailTestUtils


class TestLockedPagesView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_reports:locked_pages'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/reports/locked_pages.html')

        # Initially there should be no locked pages
        self.assertContains(response, "No locked pages found.")

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        self.page.locked_at = timezone.now()
        self.page.save()

        # Now the listing should contain our locked page
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/reports/locked_pages.html')
        self.assertNotContains(response, "No locked pages found.")
        self.assertContains(response, self.page.title)

    def test_csv_export(self):

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        if settings.USE_TZ:
            # 12:00 UTC
            self.page.locked_at = '2013-02-01T12:00:00.000Z'
            self.page.latest_revision_created_at = '2013-01-01T12:00:00.000Z'
        else:
            # 12:00 in no specific timezone
            self.page.locked_at = '2013-02-01T12:00:00'
            self.page.latest_revision_created_at = '2013-01-01T12:00:00'
        self.page.save()

        response = self.get(params={'export': 'csv'})

        # Check response
        self.assertEqual(response.status_code, 200)
        data_lines = response.getvalue().decode().split("\n")
        self.assertEqual(data_lines[0], 'Title,Updated,Status,Type,Locked At,Locked By\r')
        if settings.USE_TZ:
            self.assertEqual(data_lines[1], 'Root,2013-01-01 12:00:00+00:00,live,Page,2013-02-01 12:00:00+00:00,test@email.com\r')
        else:
            self.assertEqual(data_lines[1], 'Root,2013-01-01 12:00:00,live,Page,2013-02-01 12:00:00,test@email.com\r')

    def test_xlsx_export(self):

        self.page = Page.objects.first()
        self.page.locked = True
        self.page.locked_by = self.user
        if settings.USE_TZ:
            # 12:00 UTC
            self.page.locked_at = '2013-02-01T12:00:00.000Z'
            self.page.latest_revision_created_at = '2013-01-01T12:00:00.000Z'
        else:
            # 12:00 in no specific timezone
            self.page.locked_at = '2013-02-01T12:00:00'
            self.page.latest_revision_created_at = '2013-01-01T12:00:00'
        self.page.save()

        response = self.get(params={'export': 'xlsx'})

        # Check response - the locked page info should be in it
        self.assertEqual(response.status_code, 200)
        workbook_data = response.getvalue()
        worksheet = load_workbook(filename=BytesIO(workbook_data))['Sheet1']
        cell_array = [[cell.value for cell in row] for row in worksheet.rows]
        self.assertEqual(cell_array[0], ['Title', 'Updated', 'Status', 'Type', 'Locked At', 'Locked By'])
        self.assertEqual(cell_array[1], ['Root', datetime.datetime(2013, 1, 1, 12, 0), 'live', 'Page', datetime.datetime(2013, 2, 1, 12, 0), 'test@email.com'])
        self.assertEqual(len(cell_array), 2)


class TestFilteredLockedPagesView(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.user = self.login()
        self.unpublished_page = Page.objects.get(url_path='/home/events/tentative-unpublished-event/')
        self.unpublished_page.locked = True
        self.unpublished_page.locked_by = self.user
        self.unpublished_page.locked_at = timezone.now()
        self.unpublished_page.save()

    def get(self, params={}):
        return self.client.get(reverse('wagtailadmin_reports:locked_pages'), params)

    def test_filter_by_live(self):
        response = self.get(params={'live': 'true'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tentative Unpublished Event")
        self.assertContains(response, "My locked page")

        response = self.get(params={'live': 'false'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentative Unpublished Event")
        self.assertNotContains(response, "My locked page")

    def test_filter_by_user(self):
        response = self.get(params={'locked_by': self.user.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentative Unpublished Event")
        self.assertNotContains(response, "My locked page")


class TestFilteredLogEntriesView(TestCase, WagtailTestUtils):
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
