from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.core.models import GroupPagePermission, Page
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestModerationList(TestCase, WagtailTestUtils):
    """Test moderation list rendered by `wagtailadmin_home` view"""

    def setUp(self):
        # Create a submitter
        submitter = get_user_model().objects.create_user(
            username='submitter',
            email='submitter@email.com',
            password='password',
        )

        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Create a page
        self.page = SimplePage(
            title='Wagtail, the powerful CMS for modern websites',
            slug='wagtail',
            content='Fast, elegant, open source',
        )

        self.root_page.add_child(instance=self.page)

        # Submit it for moderation
        self.page.save_revision(user=submitter, submitted_for_moderation=True)

        # Create a revision
        self.revision = self.page.get_latest_revision()

        self.edit_page_url = reverse('wagtailadmin_pages:edit', args=(self.revision.page.id, ))
        self.preview_page_url = reverse('wagtailadmin_pages:preview_for_moderation', args=(self.revision.id, ))

    def login_as_moderator_without_edit(self):
        # Create moderators group without edit permissions
        moderators_group = Group.objects.create(name='Moderators without edit')

        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin',
            codename='access_admin'
        )

        moderators_group.permissions.add(admin_permission)

        # Create group permissions
        GroupPagePermission.objects.create(
            group=moderators_group,
            page=self.root_page,
            permission_type='publish',
        )

        # Create a moderator without edit permissions
        moderator = get_user_model().objects.create_user(
            username='moderator',
            email='moderator@email.com',
            password='password'
        )

        moderator.groups.add(moderators_group)

        self.login(moderator)

    def get(self):
        return self.client.get(reverse('wagtailadmin_home'))

    def test_edit_page(self):
        # Login as moderator
        self.login()

        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/home.html')

        # Check response
        self.assertContains(response, self.edit_page_url, count=2)

    def test_preview_for_moderation(self):
        # Login as moderator without edit permissions
        self.login_as_moderator_without_edit()

        response = self.get()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailadmin/home.html')

        # Check response
        self.assertContains(response, self.preview_page_url, count=2)
        self.assertNotContains(response, self.edit_page_url)
