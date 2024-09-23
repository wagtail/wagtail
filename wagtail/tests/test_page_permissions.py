import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings
from django.utils import timezone

from wagtail.models import (
    GroupApprovalTask,
    GroupPagePermission,
    Locale,
    Page,
    Workflow,
    WorkflowTask,
)
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.test.testapp.models import (
    BusinessSubIndex,
    CustomPermissionPage,
    CustomPermissionTester,
    EventIndex,
    EventPage,
    NoCreatableSubpageTypesPage,
    NoSubpageTypesPage,
    SingletonPageViaMaxCount,
)


class TestPagePermission(TestCase):
    fixtures = ["test.json"]

    def create_workflow_and_task(self):
        workflow = Workflow.objects.create(name="test_workflow")
        task_1 = GroupApprovalTask.objects.create(name="test_task_1")
        task_1.groups.add(Group.objects.get(name="Event moderators"))
        WorkflowTask.objects.create(
            workflow=workflow, task=task_1.task_ptr, sort_order=1
        )
        return workflow, task_1

    def test_nonpublisher_page_permissions(self):
        event_editor = get_user_model().objects.get(email="eventeditor@example.com")
        homepage = Page.objects.get(url_path="/home/")

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_creatable_subpages_page = NoCreatableSubpageTypesPage(
            title="No creatable subpages", slug="no-creatable-subpages"
        )
        homepage.add_child(instance=no_creatable_subpages_page)

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_subpages_page = NoSubpageTypesPage(title="No subpages", slug="no-subpages")
        homepage.add_child(instance=no_subpages_page)

        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )
        board_meetings_page = BusinessSubIndex.objects.get(
            url_path="/home/events/businessy-events/board-meetings/"
        )

        homepage_perms = homepage.permissions_for_user(event_editor)
        no_creatable_subpages_perms = no_creatable_subpages_page.permissions_for_user(
            event_editor
        )
        no_subpages_perms = no_subpages_page.permissions_for_user(event_editor)
        christmas_page_perms = christmas_page.permissions_for_user(event_editor)
        unpub_perms = unpublished_event_page.permissions_for_user(event_editor)
        someone_elses_event_perms = someone_elses_event_page.permissions_for_user(
            event_editor
        )
        board_meetings_perms = board_meetings_page.permissions_for_user(event_editor)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertFalse(no_creatable_subpages_perms.can_add_subpage())
        self.assertFalse(no_subpages_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())
        self.assertTrue(someone_elses_event_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertFalse(no_creatable_subpages_perms.can_edit())
        self.assertFalse(no_subpages_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())
        # basic 'add' permission doesn't allow editing pages owned by someone else
        self.assertFalse(someone_elses_event_perms.can_edit())

        self.assertFalse(homepage_perms.can_delete())
        self.assertFalse(no_creatable_subpages_perms.can_delete())
        self.assertFalse(no_subpages_perms.can_delete())
        self.assertFalse(
            christmas_page_perms.can_delete()
        )  # cannot delete because it is published
        self.assertTrue(unpub_perms.can_delete())
        self.assertFalse(someone_elses_event_perms.can_delete())

        self.assertFalse(homepage_perms.can_publish())
        self.assertFalse(no_creatable_subpages_perms.can_publish())
        self.assertFalse(no_subpages_perms.can_publish())
        self.assertFalse(christmas_page_perms.can_publish())
        self.assertFalse(unpub_perms.can_publish())

        self.assertFalse(homepage_perms.can_unpublish())
        self.assertFalse(no_creatable_subpages_perms.can_unpublish())
        self.assertFalse(no_subpages_perms.can_unpublish())
        self.assertFalse(christmas_page_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())

        self.assertFalse(homepage_perms.can_publish_subpage())
        self.assertFalse(no_creatable_subpages_perms.can_publish_subpage())
        self.assertFalse(no_subpages_perms.can_publish_subpage())
        self.assertFalse(christmas_page_perms.can_publish_subpage())
        self.assertFalse(unpub_perms.can_publish_subpage())

        self.assertFalse(homepage_perms.can_reorder_children())
        self.assertFalse(no_creatable_subpages_perms.can_reorder_children())
        self.assertFalse(no_subpages_perms.can_reorder_children())
        self.assertFalse(christmas_page_perms.can_reorder_children())
        self.assertFalse(unpub_perms.can_reorder_children())

        self.assertFalse(homepage_perms.can_move())
        self.assertFalse(no_creatable_subpages_perms.can_move())
        self.assertFalse(no_subpages_perms.can_move())
        # cannot move because this would involve unpublishing from its current location
        self.assertFalse(christmas_page_perms.can_move())
        self.assertTrue(unpub_perms.can_move())
        self.assertFalse(someone_elses_event_perms.can_move())

        # cannot move because this would involve unpublishing from its current location
        self.assertFalse(christmas_page_perms.can_move_to(unpublished_event_page))
        self.assertTrue(unpub_perms.can_move_to(christmas_page))
        self.assertFalse(
            unpub_perms.can_move_to(homepage)
        )  # no permission to create pages at destination
        self.assertFalse(
            unpub_perms.can_move_to(unpublished_event_page)
        )  # cannot make page a child of itself
        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))

        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(christmas_page))

    def test_publisher_page_permissions(self):
        event_moderator = get_user_model().objects.get(
            email="eventmoderator@example.com"
        )
        homepage = Page.objects.get(url_path="/home/")

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_creatable_subpages_page = NoCreatableSubpageTypesPage(
            title="No creatable subpages", slug="no-creatable-subpages"
        )
        homepage.add_child(instance=no_creatable_subpages_page)

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_subpages_page = NoSubpageTypesPage(title="No subpages", slug="no-subpages")
        homepage.add_child(instance=no_subpages_page)

        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        board_meetings_page = BusinessSubIndex.objects.get(
            url_path="/home/events/businessy-events/board-meetings/"
        )

        homepage_perms = homepage.permissions_for_user(event_moderator)
        no_creatable_subpages_perms = no_creatable_subpages_page.permissions_for_user(
            event_moderator
        )
        no_subpages_perms = no_subpages_page.permissions_for_user(event_moderator)
        christmas_page_perms = christmas_page.permissions_for_user(event_moderator)
        unpub_perms = unpublished_event_page.permissions_for_user(event_moderator)
        board_meetings_perms = board_meetings_page.permissions_for_user(event_moderator)

        self.assertFalse(homepage_perms.can_add_subpage())
        self.assertFalse(no_creatable_subpages_perms.can_add_subpage())
        self.assertFalse(no_subpages_perms.can_add_subpage())
        self.assertTrue(christmas_page_perms.can_add_subpage())
        self.assertTrue(unpub_perms.can_add_subpage())

        self.assertFalse(homepage_perms.can_edit())
        self.assertFalse(no_creatable_subpages_perms.can_edit())
        self.assertFalse(no_subpages_perms.can_edit())
        self.assertTrue(christmas_page_perms.can_edit())
        self.assertTrue(unpub_perms.can_edit())

        self.assertFalse(homepage_perms.can_delete())
        self.assertFalse(no_creatable_subpages_perms.can_delete())
        self.assertFalse(no_subpages_perms.can_delete())
        # can delete a published page because we have publish permission
        self.assertTrue(christmas_page_perms.can_delete())
        self.assertTrue(unpub_perms.can_delete())

        self.assertFalse(homepage_perms.can_publish())
        self.assertFalse(no_creatable_subpages_perms.can_publish())
        self.assertFalse(no_subpages_perms.can_publish())
        self.assertTrue(christmas_page_perms.can_publish())
        self.assertTrue(unpub_perms.can_publish())

        self.assertFalse(homepage_perms.can_unpublish())
        self.assertFalse(no_creatable_subpages_perms.can_unpublish())
        self.assertTrue(christmas_page_perms.can_unpublish())
        self.assertFalse(
            unpub_perms.can_unpublish()
        )  # cannot unpublish a page that isn't published

        self.assertFalse(homepage_perms.can_publish_subpage())
        self.assertFalse(no_creatable_subpages_perms.can_publish_subpage())
        self.assertFalse(no_subpages_perms.can_publish_subpage())
        self.assertTrue(christmas_page_perms.can_publish_subpage())
        self.assertTrue(unpub_perms.can_publish_subpage())

        self.assertFalse(homepage_perms.can_reorder_children())
        self.assertFalse(no_creatable_subpages_perms.can_reorder_children())
        self.assertFalse(no_subpages_perms.can_reorder_children())
        self.assertTrue(christmas_page_perms.can_reorder_children())
        self.assertTrue(unpub_perms.can_reorder_children())

        self.assertFalse(homepage_perms.can_move())
        self.assertFalse(no_creatable_subpages_perms.can_move())
        self.assertFalse(no_subpages_perms.can_move())
        self.assertTrue(christmas_page_perms.can_move())
        self.assertTrue(unpub_perms.can_move())

        self.assertTrue(christmas_page_perms.can_move_to(unpublished_event_page))
        self.assertTrue(unpub_perms.can_move_to(christmas_page))
        self.assertFalse(
            unpub_perms.can_move_to(homepage)
        )  # no permission to create pages at destination
        self.assertFalse(
            unpub_perms.can_move_to(unpublished_event_page)
        )  # cannot make page a child of itself
        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))

        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(christmas_page))

    def test_publish_page_permissions_without_edit(self):
        event_moderator = get_user_model().objects.get(
            email="eventmoderator@example.com"
        )

        # Remove 'edit' permission from the event_moderator group
        GroupPagePermission.objects.filter(
            group__name="Event moderators", permission__codename="change_page"
        ).delete()

        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        # 'someone else's event' is owned by eventmoderator
        moderator_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        homepage_perms = homepage.permissions_for_user(event_moderator)
        christmas_page_perms = christmas_page.permissions_for_user(event_moderator)
        unpub_perms = unpublished_event_page.permissions_for_user(event_moderator)
        moderator_event_perms = moderator_event_page.permissions_for_user(
            event_moderator
        )

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
        self.assertFalse(
            unpub_perms.can_unpublish()
        )  # cannot unpublish a page that isn't published

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
        event_moderator = get_user_model().objects.get(
            email="eventmoderator@example.com"
        )
        events_page = EventIndex.objects.get(url_path="/home/events/")
        events_perms = events_page.permissions_for_user(event_moderator)

        self.assertFalse(events_perms.can_delete())

    def test_can_bulk_delete_with_permissions(self):
        event_moderator = get_user_model().objects.get(
            email="eventmoderator@example.com"
        )
        events_page = EventIndex.objects.get(url_path="/home/events/")

        # Assign 'bulk_delete' permission to the event_moderator group
        event_moderators_group = Group.objects.get(name="Event moderators")
        GroupPagePermission.objects.create(
            group=event_moderators_group,
            page=events_page,
            permission_type="bulk_delete",
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
        event_editor = get_user_model().objects.get(email="eventeditor@example.com")
        events_page = EventIndex.objects.get(url_path="/home/events/")

        # Assign 'bulk_delete' permission to the event_editor group
        event_editors_group = Group.objects.get(name="Event editors")
        GroupPagePermission.objects.create(
            group=event_editors_group, page=events_page, permission_type="bulk_delete"
        )

        events_perms = events_page.permissions_for_user(event_editor)

        self.assertFalse(events_perms.can_delete())

    def test_inactive_user_has_no_permissions(self):
        user = get_user_model().objects.get(email="inactiveuser@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )

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
        user = get_user_model().objects.get(email="superuser@example.com")
        homepage = Page.objects.get(url_path="/home/").specific

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_creatable_subpages_page = NoCreatableSubpageTypesPage(
            title="No creatable subpages", slug="no-creatable-subpages"
        )
        homepage.add_child(instance=no_creatable_subpages_page)

        # As this is a direct child of the homepage, permission checks should
        # mostly mirror those for the homepage itself
        no_subpages_page = NoSubpageTypesPage(title="No subpages", slug="no-subpages")
        homepage.add_child(instance=no_subpages_page)

        root = Page.objects.get(url_path="/").specific
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        board_meetings_page = BusinessSubIndex.objects.get(
            url_path="/home/events/businessy-events/board-meetings/"
        )

        homepage_perms = homepage.permissions_for_user(user)
        no_creatable_subpages_perms = no_creatable_subpages_page.permissions_for_user(
            user
        )
        no_subpages_perms = no_subpages_page.permissions_for_user(user)
        root_perms = root.permissions_for_user(user)
        unpub_perms = unpublished_event_page.permissions_for_user(user)
        board_meetings_perms = board_meetings_page.permissions_for_user(user)

        self.assertTrue(homepage_perms.can_add_subpage())
        self.assertFalse(
            no_creatable_subpages_perms.can_add_subpage()
        )  # There are no 'creatable' subpage types
        self.assertFalse(
            no_subpages_perms.can_add_subpage()
        )  # There are no subpage types
        self.assertTrue(root_perms.can_add_subpage())

        self.assertTrue(homepage_perms.can_edit())
        self.assertTrue(no_creatable_subpages_perms.can_edit())
        self.assertTrue(no_subpages_perms.can_edit())
        self.assertFalse(
            root_perms.can_edit()
        )  # root is not a real editable page, even to superusers

        self.assertTrue(homepage_perms.can_delete())
        self.assertTrue(no_creatable_subpages_perms.can_delete())
        self.assertTrue(no_subpages_perms.can_delete())
        self.assertFalse(root_perms.can_delete())

        self.assertTrue(homepage_perms.can_publish())
        self.assertTrue(no_creatable_subpages_perms.can_publish())
        self.assertTrue(no_subpages_perms.can_publish())
        self.assertFalse(root_perms.can_publish())

        self.assertTrue(homepage_perms.can_unpublish())
        self.assertTrue(no_creatable_subpages_perms.can_unpublish())
        self.assertTrue(no_subpages_perms.can_unpublish())
        self.assertFalse(root_perms.can_unpublish())
        self.assertFalse(unpub_perms.can_unpublish())

        self.assertTrue(homepage_perms.can_publish_subpage())
        self.assertFalse(
            no_creatable_subpages_perms.can_publish_subpage()
        )  # There are no 'creatable' subpages, so a new one cannot be 'created and published' here
        self.assertFalse(
            no_subpages_perms.can_publish_subpage()
        )  # There are no subpages, so a new one cannot be 'created and published' here

        self.assertTrue(root_perms.can_publish_subpage())

        self.assertTrue(homepage_perms.can_reorder_children())
        self.assertTrue(no_creatable_subpages_perms.can_reorder_children())
        self.assertTrue(no_subpages_perms.can_reorder_children())
        self.assertTrue(root_perms.can_reorder_children())

        self.assertTrue(homepage_perms.can_move())
        self.assertTrue(no_creatable_subpages_perms.can_move())
        self.assertTrue(no_subpages_perms.can_move())
        self.assertFalse(root_perms.can_move())

        self.assertTrue(homepage_perms.can_move_to(root))
        self.assertFalse(homepage_perms.can_move_to(unpublished_event_page))

        # cannot move because the subpage_types rule of BusinessSubIndex forbids EventPage as a subpage
        self.assertFalse(unpub_perms.can_move_to(board_meetings_page))
        self.assertTrue(board_meetings_perms.can_move())
        # cannot move because the parent_page_types rule of BusinessSubIndex forbids EventPage as a parent
        self.assertFalse(board_meetings_perms.can_move_to(unpublished_event_page))

    def test_cant_move_pages_between_locales(self):
        user = get_user_model().objects.get(email="superuser@example.com")
        homepage = Page.objects.get(url_path="/home/").specific
        root = Page.objects.get(url_path="/").specific

        fr_locale = Locale.objects.create(language_code="fr")
        fr_page = root.add_child(
            instance=Page(
                title="French page",
                slug="french-page",
                locale=fr_locale,
            )
        )

        fr_homepage = root.add_child(
            instance=Page(
                title="French homepage",
                slug="french-homepage",
                locale=fr_locale,
            )
        )

        french_page_perms = fr_page.permissions_for_user(user)

        # fr_page can be moved into fr_homepage but not homepage
        self.assertFalse(french_page_perms.can_move_to(homepage))
        self.assertTrue(french_page_perms.can_move_to(fr_homepage))

        # All pages can be moved to the root, regardless what language they are
        self.assertTrue(french_page_perms.can_move_to(root))

        events_index = Page.objects.get(url_path="/home/events/")
        events_index_perms = events_index.permissions_for_user(user)
        self.assertTrue(events_index_perms.can_move_to(root))

    def test_editable_pages_for_user_with_add_permission(self):
        event_editor = get_user_model().objects.get(email="eventeditor@example.com")
        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        policy = PagePermissionPolicy()

        editable_pages = policy.instances_user_has_permission_for(
            event_editor, "change"
        )
        can_edit_pages = policy.user_has_permission(event_editor, "change")
        publishable_pages = policy.instances_user_has_permission_for(
            event_editor, "publish"
        )
        can_publish_pages = policy.user_has_permission(event_editor, "publish")

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(
            publishable_pages.filter(id=unpublished_event_page.id).exists()
        )
        self.assertFalse(
            publishable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        self.assertFalse(can_publish_pages)

    def test_explorable_pages(self):
        event_editor = get_user_model().objects.get(email="eventeditor@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )
        about_us_page = Page.objects.get(url_path="/home/about-us/")

        policy = PagePermissionPolicy()
        explorable_pages = policy.explorable_instances(event_editor)

        # Verify all pages below /home/events/ are explorable
        self.assertTrue(explorable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(explorable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(
            explorable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        # Verify page outside /events/ tree are not explorable
        self.assertFalse(explorable_pages.filter(id=about_us_page.id).exists())

    def test_explorable_pages_in_explorer(self):
        event_editor = get_user_model().objects.get(email="eventeditor@example.com")

        client = Client()
        client.force_login(event_editor)

        homepage = Page.objects.get(url_path="/home/")
        explorer_response = client.get(
            f"/admin/api/main/pages/?child_of={homepage.pk}&for_explorer=1"
        )
        explorer_json = json.loads(explorer_response.content.decode("utf-8"))

        events_page = Page.objects.get(url_path="/home/events/")
        about_us_page = Page.objects.get(url_path="/home/about-us/")

        explorable_titles = [t.get("title") for t in explorer_json.get("items")]
        self.assertIn(events_page.title, explorable_titles)
        self.assertNotIn(about_us_page.title, explorable_titles)

    def test_explorable_pages_with_permission_gap_in_hierarchy(self):
        corporate_editor = get_user_model().objects.get(
            email="corporateeditor@example.com"
        )

        policy = PagePermissionPolicy()

        about_us_page = Page.objects.get(url_path="/home/about-us/")
        businessy_events = Page.objects.get(url_path="/home/events/businessy-events/")
        events_page = Page.objects.get(url_path="/home/events/")

        explorable_pages = policy.explorable_instances(corporate_editor)

        self.assertTrue(explorable_pages.filter(id=about_us_page.id).exists())
        self.assertTrue(explorable_pages.filter(id=businessy_events.id).exists())
        self.assertTrue(explorable_pages.filter(id=events_page.id).exists())

    def test_editable_pages_for_user_with_edit_permission(self):
        event_moderator = get_user_model().objects.get(
            email="eventmoderator@example.com"
        )
        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        policy = PagePermissionPolicy()

        editable_pages = policy.instances_user_has_permission_for(
            event_moderator, "change"
        )
        can_edit_pages = policy.user_has_permission(event_moderator, "change")
        publishable_pages = policy.instances_user_has_permission_for(
            event_moderator, "publish"
        )
        can_publish_pages = policy.user_has_permission(event_moderator, "publish")

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertTrue(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(
            publishable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        self.assertTrue(can_publish_pages)

    def test_editable_pages_for_inactive_user(self):
        user = get_user_model().objects.get(email="inactiveuser@example.com")
        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        policy = PagePermissionPolicy()

        editable_pages = policy.instances_user_has_permission_for(user, "change")
        can_edit_pages = policy.user_has_permission(user, "change")
        publishable_pages = policy.instances_user_has_permission_for(user, "publish")
        can_publish_pages = policy.user_has_permission(user, "publish")

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertFalse(editable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(
            publishable_pages.filter(id=unpublished_event_page.id).exists()
        )
        self.assertFalse(
            publishable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        self.assertFalse(can_publish_pages)

    def test_editable_pages_for_superuser(self):
        user = get_user_model().objects.get(email="superuser@example.com")
        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        policy = PagePermissionPolicy()

        editable_pages = policy.instances_user_has_permission_for(user, "change")
        can_edit_pages = policy.user_has_permission(user, "change")
        publishable_pages = policy.instances_user_has_permission_for(user, "publish")
        can_publish_pages = policy.user_has_permission(user, "publish")

        self.assertTrue(editable_pages.filter(id=homepage.id).exists())
        self.assertTrue(editable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertTrue(can_edit_pages)

        self.assertTrue(publishable_pages.filter(id=homepage.id).exists())
        self.assertTrue(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertTrue(publishable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertTrue(
            publishable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        self.assertTrue(can_publish_pages)

    def test_editable_pages_for_non_editing_user(self):
        user = get_user_model().objects.get(email="admin_only_user@example.com")
        homepage = Page.objects.get(url_path="/home/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        unpublished_event_page = EventPage.objects.get(
            url_path="/home/events/tentative-unpublished-event/"
        )
        someone_elses_event_page = EventPage.objects.get(
            url_path="/home/events/someone-elses-event/"
        )

        policy = PagePermissionPolicy()

        editable_pages = policy.instances_user_has_permission_for(user, "change")
        can_edit_pages = policy.user_has_permission(user, "change")
        publishable_pages = policy.instances_user_has_permission_for(user, "publish")
        can_publish_pages = policy.user_has_permission(user, "publish")

        self.assertFalse(editable_pages.filter(id=homepage.id).exists())
        self.assertFalse(editable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(editable_pages.filter(id=unpublished_event_page.id).exists())
        self.assertFalse(editable_pages.filter(id=someone_elses_event_page.id).exists())

        self.assertFalse(can_edit_pages)

        self.assertFalse(publishable_pages.filter(id=homepage.id).exists())
        self.assertFalse(publishable_pages.filter(id=christmas_page.id).exists())
        self.assertFalse(
            publishable_pages.filter(id=unpublished_event_page.id).exists()
        )
        self.assertFalse(
            publishable_pages.filter(id=someone_elses_event_page.id).exists()
        )

        self.assertFalse(can_publish_pages)

    def test_lock_page_for_superuser(self):
        user = get_user_model().objects.get(email="superuser@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        locked_page = Page.objects.get(url_path="/home/my-locked-page/")

        perms = christmas_page.permissions_for_user(user)
        locked_perms = locked_page.permissions_for_user(user)

        self.assertTrue(perms.can_lock())
        self.assertFalse(
            locked_perms.can_unpublish()
        )  # locked pages can't be unpublished
        self.assertTrue(perms.can_unlock())

    def test_lock_page_for_moderator(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        perms = christmas_page.permissions_for_user(user)

        self.assertTrue(perms.can_lock())
        self.assertTrue(perms.can_unlock())

    def test_lock_page_for_moderator_without_unlock_permission(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        GroupPagePermission.objects.filter(
            group__name="Event moderators", permission__codename="unlock_page"
        ).delete()

        perms = christmas_page.permissions_for_user(user)

        self.assertTrue(perms.can_lock())
        self.assertFalse(perms.can_unlock())

    def test_lock_page_for_moderator_whole_locked_page_without_unlock_permission(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # Lock the page
        christmas_page.locked = True
        christmas_page.locked_by = user
        christmas_page.locked_at = timezone.now()
        christmas_page.save()

        GroupPagePermission.objects.filter(
            group__name="Event moderators", permission__codename="unlock_page"
        ).delete()

        perms = christmas_page.permissions_for_user(user)

        # Unlike in the previous test, the user can unlock this page as it was them who locked
        self.assertTrue(perms.can_lock())
        self.assertTrue(perms.can_unlock())

    def test_lock_page_for_editor(self):
        user = get_user_model().objects.get(email="eventeditor@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        perms = christmas_page.permissions_for_user(user)

        self.assertFalse(perms.can_lock())
        self.assertFalse(perms.can_unlock())

    def test_lock_page_for_non_editing_user(self):
        user = get_user_model().objects.get(email="admin_only_user@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        perms = christmas_page.permissions_for_user(user)

        self.assertFalse(perms.can_lock())
        self.assertFalse(perms.can_unlock())

    def test_lock_page_for_editor_with_lock_permission(self):
        user = get_user_model().objects.get(email="eventeditor@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Event editors"),
            page=christmas_page,
            permission_type="lock",
        )

        perms = christmas_page.permissions_for_user(user)

        self.assertTrue(perms.can_lock())

        # Still shouldn't have unlock permission
        self.assertFalse(perms.can_unlock())

    def test_page_locked_for_unlocked_page(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        perms = christmas_page.permissions_for_user(user)

        self.assertFalse(perms.page_locked())

    def test_page_locked_for_locked_page(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # Lock the page
        christmas_page.locked = True
        christmas_page.locked_by = user
        christmas_page.locked_at = timezone.now()
        christmas_page.save()

        perms = christmas_page.permissions_for_user(user)

        # The user who locked the page shouldn't see the page as locked
        self.assertFalse(perms.page_locked())

        # Other users should see the page as locked
        other_user = get_user_model().objects.get(email="eventeditor@example.com")

        other_perms = christmas_page.permissions_for_user(other_user)
        self.assertTrue(other_perms.page_locked())

    @override_settings(WAGTAILADMIN_GLOBAL_EDIT_LOCK=True)
    def test_page_locked_for_locked_page_with_global_lock_enabled(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # Lock the page
        christmas_page.locked = True
        christmas_page.locked_by = user
        christmas_page.locked_at = timezone.now()
        christmas_page.save()

        perms = christmas_page.permissions_for_user(user)

        # The user who locked the page should now also see the page as locked
        self.assertTrue(perms.page_locked())

        # Other users should see the page as locked, like before
        other_user = get_user_model().objects.get(email="eventeditor@example.com")

        other_perms = christmas_page.permissions_for_user(other_user)

        self.assertTrue(other_perms.page_locked())

    def test_page_locked_in_workflow(self):
        workflow, task = self.create_workflow_and_task()
        editor = get_user_model().objects.get(email="eventeditor@example.com")
        moderator = get_user_model().objects.get(email="eventmoderator@example.com")
        superuser = get_user_model().objects.get(email="superuser@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        christmas_page.save_revision()
        workflow.start(christmas_page, editor)

        moderator_perms = christmas_page.permissions_for_user(moderator)

        # the moderator is in the group assigned to moderate the task, so the page should
        # not be locked for them
        self.assertFalse(moderator_perms.page_locked())

        superuser_perms = christmas_page.permissions_for_user(superuser)

        # superusers can moderate any GroupApprovalTask, so the page should not be locked
        # for them
        self.assertFalse(superuser_perms.page_locked())

        editor_perms = christmas_page.permissions_for_user(editor)

        # the editor is not in the group assigned to moderate the task, so the page should
        # be locked for them
        self.assertTrue(editor_perms.page_locked())

    def test_page_lock_in_workflow(self):
        workflow, task = self.create_workflow_and_task()
        editor = get_user_model().objects.get(email="eventeditor@example.com")
        moderator = get_user_model().objects.get(email="eventmoderator@example.com")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")
        christmas_page.save_revision()
        workflow.start(christmas_page, editor)

        moderator_perms = christmas_page.permissions_for_user(moderator)

        # the moderator is in the group assigned to moderate the task, so they can lock the page, but can't unlock it
        # unless they're the locker
        self.assertTrue(moderator_perms.can_lock())
        self.assertFalse(moderator_perms.can_unlock())

        editor_perms = christmas_page.permissions_for_user(editor)

        # the editor is not in the group assigned to moderate the task, so they can't lock or unlock the page
        self.assertFalse(editor_perms.can_lock())
        self.assertFalse(editor_perms.can_unlock())

    def test_custom_permission_tester_page(self):
        homepage = Page.objects.get(url_path="/home/")
        instance = CustomPermissionPage(
            title="This page has a custom permission tester",
            slug="page-with-custom-permission-tester",
        )
        homepage.add_child(instance=instance)
        page = Page.objects.get(pk=instance.pk)
        user = get_user_model().objects.get(email="eventeditor@example.com")
        self.assertIsInstance(page.permissions_for_user(user), CustomPermissionTester)


class TestPagePermissionTesterCanCopyTo(TestCase):
    """Tests PagePermissionTester.can_copy_to()"""

    fixtures = ["test.json"]

    def setUp(self):
        # These same pages will be used for testing the result for each user
        self.board_meetings_page = BusinessSubIndex.objects.get(
            url_path="/home/events/businessy-events/board-meetings/"
        )
        self.event_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # We'll also create a SingletonPageViaMaxCount to use
        homepage = Page.objects.get(url_path="/home/")
        self.singleton_page = SingletonPageViaMaxCount(title="there can be only one")
        homepage.add_child(instance=self.singleton_page)

    def test_inactive_user_cannot_copy_any_pages(self):
        user = get_user_model().objects.get(email="inactiveuser@example.com")

        # Create PagePermissionTester objects for this user, for each page
        board_meetings_page_perms = self.board_meetings_page.permissions_for_user(user)
        event_page_perms = self.event_page.permissions_for_user(user)
        singleton_page_perms = self.singleton_page.permissions_for_user(user)

        # This user should not be able to copy any pages
        self.assertFalse(event_page_perms.can_copy_to(self.event_page.get_parent()))
        self.assertFalse(
            board_meetings_page_perms.can_copy_to(self.board_meetings_page.get_parent())
        )
        self.assertFalse(
            singleton_page_perms.can_copy_to(self.singleton_page.get_parent())
        )

    def test_no_permissions_admin_cannot_copy_any_pages(self):
        user = get_user_model().objects.get(email="admin_only_user@example.com")

        # Create PagePermissionTester objects for this user, for each page
        board_meetings_page_perms = self.board_meetings_page.permissions_for_user(user)
        event_page_perms = self.event_page.permissions_for_user(user)
        singleton_page_perms = self.singleton_page.permissions_for_user(user)

        # This user should not be able to copy any pages
        self.assertFalse(event_page_perms.can_copy_to(self.event_page.get_parent()))
        self.assertFalse(
            board_meetings_page_perms.can_copy_to(self.board_meetings_page.get_parent())
        )
        self.assertFalse(
            singleton_page_perms.can_copy_to(self.singleton_page.get_parent())
        )

    def test_event_moderator_cannot_copy_a_singleton_page(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")

        # Create PagePermissionTester objects for this user, for each page
        board_meetings_page_perms = self.board_meetings_page.permissions_for_user(user)
        event_page_perms = self.event_page.permissions_for_user(user)
        singleton_page_perms = self.singleton_page.permissions_for_user(user)

        # We'd expect an event moderator to be able to copy an event page
        self.assertTrue(event_page_perms.can_copy_to(self.event_page.get_parent()))
        # This works because copying doesn't necessarily have to mean publishing
        self.assertTrue(
            board_meetings_page_perms.can_copy_to(self.board_meetings_page.get_parent())
        )
        # SingletonPageViaMaxCount.can_create_at() prevents copying, regardless of a user's permissions
        self.assertFalse(
            singleton_page_perms.can_copy_to(self.singleton_page.get_parent())
        )

    def test_not_even_a_superuser_can_copy_a_singleton_page(self):
        user = get_user_model().objects.get(email="superuser@example.com")

        # Create PagePermissionTester object for this user, for each page
        board_meetings_page_perms = self.board_meetings_page.permissions_for_user(user)
        event_page_perms = self.event_page.permissions_for_user(user)
        singleton_page_perms = self.singleton_page.permissions_for_user(user)

        # A superuser has full permissions, so these are self explanatory
        self.assertTrue(event_page_perms.can_copy_to(self.event_page.get_parent()))
        self.assertTrue(
            board_meetings_page_perms.can_copy_to(self.board_meetings_page.get_parent())
        )
        # However, SingletonPageViaMaxCount.can_create_at() prevents copying, regardless of a user's permissions
        self.assertFalse(
            singleton_page_perms.can_copy_to(self.singleton_page.get_parent())
        )


class TestPagePermissionModel(TestCase):
    fixtures = [
        "test.json",
    ]

    def test_create_with_permission_type_only(self):
        user = get_user_model().objects.get(email="eventmoderator@example.com")
        page = Page.objects.get(url_path="/home/secret-plans/steal-underpants/")
        group_permission = GroupPagePermission.objects.create(
            group=user.groups.first(), page=page, permission_type="add"
        )
        self.assertEqual(group_permission.permission.codename, "add_page")
