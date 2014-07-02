from six import StringIO

from django.test import TestCase, Client
from django.http import HttpRequest, Http404
from django.core import management
from django.contrib.auth.models import User

from wagtail.wagtailcore.models import Page, Site, UserPagePermissionsProxy
from wagtail.tests.models import EventPage, EventIndex, SimplePage


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

        user_perms = UserPagePermissionsProxy(event_editor)
        editable_pages = user_perms.editable_pages()
        can_edit_pages = user_perms.can_edit_pages()
        publishable_pages = user_perms.publishable_pages()
        can_publish_pages = user_perms.can_publish_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_publish_pages)

    def test_editable_pages_for_user_with_edit_permission(self):
        event_moderator = User.objects.get(username='eventmoderator')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        user_perms = UserPagePermissionsProxy(event_moderator)
        editable_pages = user_perms.editable_pages()
        can_edit_pages = user_perms.can_edit_pages()
        publishable_pages = user_perms.publishable_pages()
        can_publish_pages = user_perms.can_publish_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertTrue(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_publish_pages)

    def test_editable_pages_for_inactive_user(self):
        user = User.objects.get(username='inactiveuser')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        user_perms = UserPagePermissionsProxy(user)
        editable_pages = user_perms.editable_pages()
        can_edit_pages = user_perms.can_edit_pages()
        publishable_pages = user_perms.publishable_pages()
        can_publish_pages = user_perms.can_publish_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertFalse(editable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_publish_pages)

    def test_editable_pages_for_superuser(self):
        user = User.objects.get(username='superuser')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        user_perms = UserPagePermissionsProxy(user)
        editable_pages = user_perms.editable_pages()
        can_edit_pages = user_perms.can_edit_pages()
        publishable_pages = user_perms.publishable_pages()
        can_publish_pages = user_perms.can_publish_pages()

        self.assertTrue(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertTrue(publishable_pages.filter(id=homepage.id).exists())
        self.assertTrue(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_publish_pages)

    def test_editable_pages_for_non_editing_user(self):
        user = User.objects.get(username='admin_only_user')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        user_perms = UserPagePermissionsProxy(user)
        editable_pages = user_perms.editable_pages()
        can_edit_pages = user_perms.can_edit_pages()
        publishable_pages = user_perms.publishable_pages()
        can_publish_pages = user_perms.can_publish_pages()

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertFalse(editable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(publishable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_publish_pages)
