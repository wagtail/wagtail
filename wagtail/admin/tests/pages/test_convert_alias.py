import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import Page, PageLogEntry
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestConvertAlias(TestCase, WagtailTestUtils):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(title="Hello world!", slug="hello-world", content="hello")
        self.root_page.add_child(instance=self.child_page)

        # Add alias page
        self.alias_page = self.child_page.create_alias(update_slug='alias-page')

        # Login
        self.user = self.login()

    def test_convert_alias(self):
        response = self.client.get(reverse('wagtailadmin_pages:convert_alias', args=[self.alias_page.id]))
        self.assertEqual(response.status_code, 200)

    def test_convert_alias_not_alias(self):
        response = self.client.get(reverse('wagtailadmin_pages:convert_alias', args=[self.child_page.id]))
        self.assertEqual(response.status_code, 404)

    def test_convert_alias_bad_permission(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.get(reverse('wagtailadmin_pages:convert_alias', args=[self.alias_page.id]))

        # Check that the user received a permission denied response
        self.assertRedirects(response, '/admin/')

    def test_post_convert_alias(self):
        response = self.client.post(reverse('wagtailadmin_pages:convert_alias', args=[self.alias_page.id]))

        # User should be redirected to the edit view of the converted page
        self.assertRedirects(response, reverse('wagtailadmin_pages:edit', args=[self.alias_page.id]))

        # Check the page was converted
        self.alias_page.refresh_from_db()
        self.assertIsNone(self.alias_page.alias_of)

        # Check that a revision was created
        revision = self.alias_page.revisions.get()
        self.assertEqual(revision.user, self.user)
        self.assertEqual(self.alias_page.live_revision, revision)

        # Check audit log
        log = PageLogEntry.objects.get(action='wagtail.convert_alias')
        self.assertFalse(log.content_changed)
        self.assertEqual(json.loads(log.data_json), {"page": {"id": self.alias_page.id, "title": self.alias_page.get_admin_display_title()}})
        self.assertEqual(log.page, self.alias_page.page_ptr)
        self.assertEqual(log.revision, revision)
        self.assertEqual(log.user, self.user)
