from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from wagtail.core.log_actions import LogActionRegistry
from wagtail.core.models import (
    Page, PageLogEntry, PageViewRestriction, Task, Workflow, WorkflowTask)
from wagtail.tests.testapp.models import SimplePage
from wagtail.tests.utils import WagtailTestUtils


class TestAuditLogManager(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.create_superuser(
            username='administrator',
            email='administrator@email.com',
            password='password'
        )
        self.page = Page.objects.get(pk=1)
        self.simple_page = self.page.add_child(
            instance=SimplePage(title="Simple page", slug="simple", content="Hello", owner=self.user)
        )

    def test_log_action(self):
        now = timezone.now()

        with freeze_time(now):
            entry = PageLogEntry.objects.log_action(
                self.page, 'wagtail.edit', user=self.user
            )

        self.assertEqual(entry.content_type, self.page.content_type)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.timestamp, now)

    def test_get_for_model(self):
        PageLogEntry.objects.log_action(self.page, 'wagtail.edit')
        PageLogEntry.objects.log_action(self.simple_page, 'wagtail.edit')

        entries = PageLogEntry.objects.get_for_model(SimplePage)
        self.assertEqual(entries.count(), 2)
        self.assertListEqual(
            list(entries),
            list(PageLogEntry.objects.filter(page=self.simple_page))
        )

    def test_get_for_user(self):
        self.assertEqual(PageLogEntry.objects.get_for_user(self.user).count(), 1)  # the create from setUp


class TestAuditLog(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=1)

        self.home_page = self.root_page.add_child(
            instance=SimplePage(title="Homepage", slug="home2", content="hello")
        )

        PageLogEntry.objects.all().delete()  # clean up the log entries here.

    def test_page_create(self):
        self.assertEqual(PageLogEntry.objects.count(), 0)  # homepage

        page = self.home_page.add_child(
            instance=SimplePage(title="Hello", slug="my-page", content="world")
        )
        self.assertEqual(PageLogEntry.objects.count(), 1)
        log_entry = PageLogEntry.objects.order_by('pk').last()
        self.assertEqual(log_entry.action, 'wagtail.create')
        self.assertEqual(log_entry.page_id, page.id)
        self.assertEqual(log_entry.content_type, page.content_type)
        self.assertEqual(log_entry.label, page.get_admin_display_title())

    def test_page_edit(self):
        # Directly saving a revision should not yield a log entry
        self.home_page.save_revision()
        self.assertEqual(PageLogEntry.objects.count(), 0)

        # Explicitly ask to record the revision change
        self.home_page.save_revision(log_action=True)
        self.assertEqual(PageLogEntry.objects.count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.edit').count(), 1)

        # passing a string for the action should log this.
        self.home_page.save_revision(log_action='wagtail.revert')
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.revert').count(), 1)

    def test_page_publish(self):
        revision = self.home_page.save_revision()
        revision.publish()
        self.assertEqual(PageLogEntry.objects.count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.publish').count(), 1)

    def test_page_rename(self):
        # Should not log a name change when publishing the first revision
        revision = self.home_page.save_revision()
        self.home_page.title = "Old title"
        self.home_page.save()
        revision.publish()

        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.publish').count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.rename').count(), 0)

        # Now, check the rename is logged
        revision = self.home_page.save_revision()
        self.home_page.title = "New title"
        self.home_page.save()
        revision.publish()

        self.assertEqual(PageLogEntry.objects.count(), 3)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.publish').count(), 2)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.rename').count(), 1)

    def test_page_unpublish(self):
        self.home_page.unpublish()
        self.assertEqual(PageLogEntry.objects.count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.unpublish').count(), 1)

    def test_revision_revert(self):
        revision1 = self.home_page.save_revision()
        self.home_page.save_revision()

        self.home_page.save_revision(log_action=True, previous_revision=revision1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.revert').count(), 1)

    def test_revision_schedule_publish(self):
        go_live_at = datetime.now() + timedelta(days=1)
        if settings.USE_TZ:
            go_live_at = timezone.make_aware(go_live_at)
        self.home_page.go_live_at = go_live_at

        # with no live revision
        revision = self.home_page.save_revision()
        revision.publish()

        log_entries = PageLogEntry.objects.filter(action='wagtail.publish.schedule')
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries[0].data['revision']['id'], revision.id)
        self.assertEqual(log_entries[0].data['revision']['go_live_at'], go_live_at.strftime("%d %b %Y %H:%M"))

    def test_revision_schedule_revert(self):
        revision1 = self.home_page.save_revision()
        revision2 = self.home_page.save_revision()

        if settings.USE_TZ:
            self.home_page.go_live_at = timezone.make_aware(datetime.now() + timedelta(days=1))
        else:
            self.home_page.go_live_at = datetime.now() + timedelta(days=1)

        schedule_revision = self.home_page.save_revision(log_action=True, previous_revision=revision2)
        schedule_revision.publish(previous_revision=revision1)

        self.assertListEqual(
            list(PageLogEntry.objects.values_list('action', flat=True)),
            ['wagtail.publish.schedule', 'wagtail.revert']  # order_by -timestamp, by default
        )

    def test_revision_cancel_schedule(self):
        if settings.USE_TZ:
            self.home_page.go_live_at = timezone.make_aware(datetime.now() + timedelta(days=1))
        else:
            self.home_page.go_live_at = datetime.now() + timedelta(days=1)
        revision = self.home_page.save_revision()
        revision.publish()

        revision.approved_go_live_at = None
        revision.save(update_fields=['approved_go_live_at'])

        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.schedule.cancel').count(), 1)

    def test_page_lock_unlock(self):
        self.home_page.save(log_action='wagtail.lock')
        self.home_page.save(log_action='wagtail.unlock')

        self.assertEqual(PageLogEntry.objects.filter(action__in=['wagtail.lock', 'wagtail.unlock']).count(), 2)

    def test_page_copy(self):
        self.home_page.copy(update_attrs={'title': "About us", 'slug': 'about-us'})

        self.assertListEqual(
            list(PageLogEntry.objects.values_list('action', flat=True)),
            ['wagtail.publish', 'wagtail.copy', 'wagtail.create']
        )

    def test_page_reorder(self):
        section_1 = self.root_page.add_child(
            instance=SimplePage(title="Child 1", slug="child-1", content="hello")
        )
        self.root_page.add_child(
            instance=SimplePage(title="Child 2", slug="child-2", content="hello")
        )

        user = get_user_model().objects.first()

        # Reorder section 1 to be the last page under root_page.
        # This should log as `wagtail.reorder` because the page was moved under the same parent page
        section_1.move(self.root_page, user=user, pos="last-child")

        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.reorder', user=user).count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.move', user=user).count(), 0)

    def test_page_move(self):
        section = self.root_page.add_child(
            instance=SimplePage(title="About us", slug="about", content="hello")
        )
        user = get_user_model().objects.first()
        section.move(self.home_page, user=user)

        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.move', user=user).count(), 1)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.reorder', user=user).count(), 0)

    def test_page_delete(self):
        self.home_page.add_child(
            instance=SimplePage(title="Child", slug="child-page", content="hello")
        )
        child = self.home_page.add_child(
            instance=SimplePage(title="Another child", slug="child-page-2", content="hello")
        )

        child.delete()
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.delete').count(), 1)

        # check deleting a parent page logs child deletion
        self.home_page.delete()
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.delete').count(), 3)
        self.assertListEqual(
            list(PageLogEntry.objects.filter(action='wagtail.delete').values_list('label', flat=True)),
            ['Homepage (simple page)', 'Child (simple page)', 'Another child (simple page)']
        )

    def test_workflow_actions(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task_1 = Task.objects.create(name='test_task_1')
        task_2 = Task.objects.create(name='test_task_2')
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)

        self.home_page.save_revision()
        user = get_user_model().objects.first()
        workflow_state = workflow.start(self.home_page, user)

        workflow_entry = PageLogEntry.objects.filter(action='wagtail.workflow.start')
        self.assertEqual(workflow_entry.count(), 1)
        self.assertEqual(workflow_entry[0].data, {
            'workflow': {
                'id': workflow.id,
                'title': workflow.name,
                'status': workflow_state.status,
                'task_state_id': workflow_state.current_task_state_id,
                'next': {
                    'id': workflow_state.current_task_state.task.id,
                    'title': workflow_state.current_task_state.task.name,
                },
            }
        })

        # Approve
        for action in ['approve', 'reject']:
            with self.subTest(action):
                task_state = workflow_state.current_task_state
                task_state.task.on_action(task_state, user=None, action_name=action)
                workflow_state.refresh_from_db()

                entry = PageLogEntry.objects.filter(action='wagtail.workflow.{}'.format(action))
                self.assertEqual(entry.count(), 1)
                self.assertEqual(entry[0].data, {
                    'workflow': {
                        'id': workflow.id,
                        'title': workflow.name,
                        'status': task_state.status,
                        'task_state_id': task_state.id,
                        'task': {
                            'id': task_state.task.id,
                            'title': task_state.task.name,
                        },
                        'next': {
                            'id': workflow_state.current_task_state.task.id,
                            'title': workflow_state.current_task_state.task.name,
                        },
                    },
                    'comment': '',
                })

    def test_workflow_completions_logs_publishing_user(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task_1 = Task.objects.create(name='test_task_1')
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)

        self.assertFalse(PageLogEntry.objects.filter(action='wagtail.publish').exists())

        self.home_page.save_revision()
        user = get_user_model().objects.first()
        workflow_state = workflow.start(self.home_page, user)

        publisher = get_user_model().objects.last()
        task_state = workflow_state.current_task_state
        task_state.task.on_action(task_state, user=None, action_name='approve')

        self.assertEqual(PageLogEntry.objects.get(action='wagtail.publish').user, publisher)

    def test_page_privacy(self):
        restriction = PageViewRestriction.objects.create(page=self.home_page)
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.view_restriction.create').count(), 1)
        restriction.restriction_type = PageViewRestriction.PASSWORD
        restriction.save()
        self.assertEqual(PageLogEntry.objects.filter(action='wagtail.view_restriction.edit').count(), 1)


def test_hook(actions):
    return actions.register_action('test.custom_action', 'Custom action', 'Tested!')


class TestAuditLogHooks(TestCase, WagtailTestUtils):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

    def test_register_log_actions_hook(self):
        # testapp/wagtail_hooks.py defines a 'blockquote' rich text feature with a hallo.js
        # plugin, via the register_rich_text_features hook; test that we can retrieve it here
        log_actions = LogActionRegistry('register_log_actions')
        actions = log_actions.get_actions()
        self.assertIn('wagtail.create', actions)

    def test_action_must_be_registered(self):
        # We check actions are registered to let developers know if they have forgotten to register
        # a new action or made a spelling mistake. It's not intended as a database-level constraint.
        with self.assertRaises(ValidationError) as e:
            PageLogEntry.objects.log_action(self.root_page, action='test.custom_action')

        self.assertEqual(e.exception.message_dict, {
            'action': ["The log action 'test.custom_action' has not been registered."]
        })

    def test_action_format_message(self):
        # All new logs should pass our validation, but older logs or logs that were added in bulk
        # may be invalid.
        # Using LogEntry.objects.update, we can bypass the on save validation.
        log_entry = PageLogEntry.objects.log_action(self.root_page, action='wagtail.create')
        PageLogEntry.objects.update(action='test.custom_action')
        log_entry.refresh_from_db()

        log_actions = LogActionRegistry('register_log_actions')
        self.assertEqual(log_actions.format_message(log_entry), "Unknown test.custom_action")
        self.assertNotIn('test.custom_action', log_actions.get_actions())

        with self.register_hook('register_log_actions', test_hook):
            log_actions = LogActionRegistry('register_log_actions')
            self.assertIn('test.custom_action', log_actions.get_actions())
            self.assertEqual(log_actions.format_message(log_entry), "Tested!")
            self.assertEqual(log_actions.get_action_label('test.custom_action'), 'Custom action')
