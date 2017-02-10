from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.tests.testapp.models import BusinessSubIndex, EventIndex, EventPage
from wagtail.wagtailcore.models import GroupPagePermission, Page, UserPagePermissionsProxy


class TestPagePermission(TestCase):
    fixtures = ['test.json']

    def test_nonpublisher_page_permissions(self):
        event_editor = get_user_model().objects.get(username='eventeditor')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        someone_elses_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')
        board_meetings_page = BusinessSubIndex.objects.get(url_path='/home/events/businessy-events/board-meetings/')

        homepage_perms = homepage.permissions_for_user(event_editor)
        christmas_page_perms = christmas_page.permissions_for_user(event_editor)
        unpub_perms = unpublished_event_page.permissions_for_user(event_editor)
        someone_elses_event_perms = someone_elses_event_page.permissions_for_user(event_editor)
        board_meetings_perms = board_meetings_page.permissions_for_user(event_editor)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())
        self.assertTrue(someone_elses_event_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())
        # basic 'add' permission doesn't allow editing pages owned by someone else
        self.assertFalse(someone_elses_event_perms.can_edit())

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
        # cannot move because this would involve unpublishing from its current location
        self.assertFalse(christmas_page_perms.can_move())
        self.assertTrue(unpub_perms.can_move())
        self.assertFalse(someone_elses_event_perms.can_move())

        # cannot move because this would involve unpublishing from its current location
        self.assertFalse(christmas_page_perms.can_move_to(unpublished_event_page))
        self.assertTrue(unpub_perms.can_move_to(christmas_page))
        self.assertFalse(unpub_perms.can_move_to(homepage))  # no permission to create pages at destination
        self.assertFalse(unpub_perms.can_move_to(unpublished_event_page))  # cannot make page a child of itself
        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))

        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(christmas_page))

    def test_publisher_page_permissions(self):
        event_moderator = get_user_model().objects.get(username='eventmoderator')
        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        board_meetings_page = BusinessSubIndex.objects.get(url_path='/home/events/businessy-events/board-meetings/')

        homepage_perms = homepage.permissions_for_user(event_moderator)
        christmas_page_perms = christmas_page.permissions_for_user(event_moderator)
        unpub_perms = unpublished_event_page.permissions_for_user(event_moderator)
        board_meetings_perms = board_meetings_page.permissions_for_user(event_moderator)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())

        self.assertFalse(homepage_perms.can_delete())
        # can delete a published page because we have publish permission
        self.assertTrue(christmas_page_perms.can_delete())
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
        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))

        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(christmas_page))

    def test_publish_page_permissions_without_edit(self):
        event_moderator = get_user_model().objects.get(username='eventmoderator')

        # Remove 'edit' permission from the event_moderator group
        GroupPagePermission.objects.filter(group__name='Event moderators', permission_type='edit').delete()

        homepage = Page.objects.get(url_path='/home/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        # 'someone else's event' is owned by eventmoderator
        moderator_event_page = EventPage.objects.get(url_path='/home/events/someone-elses-event/')

        homepage_perms = homepage.permissions_for_user(event_moderator)
        christmas_page_perms = christmas_page.permissions_for_user(event_moderator)
        unpub_perms = unpublished_event_page.permissions_for_user(event_moderator)
        moderator_event_perms = moderator_event_page.permissions_for_user(event_moderator)

        # we still have add permission within events
        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())

        # add permission lets us edit our own event
        self.assertFalse(christmas_page_perms.can_edit())
        self.assertTrue(moderator_event_perms.can_edit())

        # with add + publish permissions, can delete a published page owned by us
        self.assertTrue(moderator_event_perms.can_delete())
        # but NOT a page owned by someone else (which would require edit permission)
        self.assertFalse(christmas_page_perms.can_delete())
        # ...even an unpublished one
        self.assertFalse(unpub_perms.can_delete())

        # we can still publish/unpublish events regardless of owner
        self.assertFalse(homepage_perms.can_publish())
        self.assertTrue(christmas_page_perms.can_publish())
        self.assertTrue(unpub_perms.can_publish())

        self.assertFalse(homepage_perms.can_unpublish())
        self.assertTrue(christmas_page_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())  # cannot unpublish a page that isn't published

        self.assertFalse(homepage_perms.can_publish_subpage())
        self.assertTrue(christmas_page_perms.can_publish_subpage())
        self.assertTrue(unpub_perms.can_publish_subpage())

        # reorder permission is considered equivalent to publish permission
        # (so we can do it on pages we can't edit)
        self.assertFalse(homepage_perms.can_reorder_children())
        self.assertTrue(christmas_page_perms.can_reorder_children())
        self.assertTrue(unpub_perms.can_reorder_children())

        # moving requires edit permission
        self.assertFalse(homepage_perms.can_move())
        self.assertFalse(christmas_page_perms.can_move())
        self.assertTrue(moderator_event_perms.can_move())
        # and add permission on the destination
        self.assertFalse(moderator_event_perms.can_move_to(homepage))
        self.assertTrue(moderator_event_perms.can_move_to(unpublished_event_page))

    def test_cannot_bulk_delete_without_permissions(self):
        event_moderator = get_user_model().objects.get(username='eventmoderator')
        events_page = EventIndex.objects.get(url_path='/home/events/')
        events_perms = events_page.permissions_for_user(event_moderator)

        self.assertFalse(events_perms.can_delete())

    def test_can_bulk_delete_with_permissions(self):
        event_moderator = get_user_model().objects.get(username='eventmoderator')
        events_page = EventIndex.objects.get(url_path='/home/events/')

        # Assign 'bulk_delete' permission to the event_moderator group
        event_moderators_group = Group.objects.get(name='Event moderators')
        GroupPagePermission.objects.create(
            group=event_moderators_group, page=events_page, permission_type='bulk_delete'
        )

        events_perms = events_page.permissions_for_user(event_moderator)

        self.assertTrue(events_perms.can_delete())

    def test_need_delete_permission_to_bulk_delete(self):
        """
        Having bulk_delete permission is not in itself sufficient to allow deleting pages -
        you need actual edit permission on the pages too.

        In this test the event editor is given bulk_delete permission, but since their
        only other permission is 'add', they cannot delete published pages or pages owned
        by other users, and therefore the bulk deletion cannot happen.
        """
        event_editor = get_user_model().objects.get(username='eventeditor')
        events_page = EventIndex.objects.get(url_path='/home/events/')

        # Assign 'bulk_delete' permission to the event_editor group
        event_editors_group = Group.objects.get(name='Event editors')
        GroupPagePermission.objects.create(
            group=event_editors_group, page=events_page, permission_type='bulk_delete'
        )

        events_perms = events_page.permissions_for_user(event_editor)

        self.assertFalse(events_perms.can_delete())

    def test_inactive_user_has_no_permissions(self):
        user = get_user_model().objects.get(username='inactiveuser')
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
        user = get_user_model().objects.get(username='superuser')
        homepage = Page.objects.get(url_path='/home/').specific
        root = Page.objects.get(url_path='/').specific
        unpublished_event_page = EventPage.objects.get(url_path='/home/events/tentative-unpublished-event/')
        board_meetings_page = BusinessSubIndex.objects.get(url_path='/home/events/businessy-events/board-meetings/')

        homepage_perms = homepage.permissions_for_user(user)
        root_perms = root.permissions_for_user(user)
        unpub_perms = unpublished_event_page.permissions_for_user(user)
        board_meetings_perms = board_meetings_page.permissions_for_user(user)

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

        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))
        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(unpublished_event_page))

    def test_editable_pages_for_user_with_add_permission(self):
        event_editor = get_user_model().objects.get(username='eventeditor')
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
        event_moderator = get_user_model().objects.get(username='eventmoderator')
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
        user = get_user_model().objects.get(username='inactiveuser')
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
        user = get_user_model().objects.get(username='superuser')
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
        user = get_user_model().objects.get(username='admin_only_user')
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

    def test_lock_page_for_superuser(self):
        user = get_user_model().objects.get(username='superuser')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        locked_page = Page.objects.get(url_path='/home/my-locked-page/')

        perms = UserPagePermissionsProxy(user).for_page(christmas_page)
        locked_perms = UserPagePermissionsProxy(user).for_page(locked_page)

        self.assertTrue(perms.can_lock())
        self.assertFalse(locked_perms.can_unpublish())  # locked pages can't be unpublished

    def test_lock_page_for_moderator(self):
        user = get_user_model().objects.get(username='eventmoderator')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

        perms = UserPagePermissionsProxy(user).for_page(christmas_page)

        self.assertTrue(perms.can_lock())

    def test_lock_page_for_editor(self):
        user = get_user_model().objects.get(username='eventeditor')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

        perms = UserPagePermissionsProxy(user).for_page(christmas_page)

        self.assertFalse(perms.can_lock())

    def test_lock_page_for_non_editing_user(self):
        user = get_user_model().objects.get(username='admin_only_user')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

        perms = UserPagePermissionsProxy(user).for_page(christmas_page)

        self.assertFalse(perms.can_lock())
