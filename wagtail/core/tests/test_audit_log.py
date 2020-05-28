from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from wagtail.core.models import LogEntry, Page, PageViewRestriction, Task, Workflow, WorkflowTask
from wagtail.tests.testapp.models import SimplePage


class TestAuditLogManager(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
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
            entry = LogEntry.objects.log_action(
                self.page, 'test', user=self.user
            )

        self.assertEqual(entry.content_type, self.page.content_type)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.timestamp, now)

    def test_get_for_model(self):
        LogEntry.objects.log_action(self.page, 'test')
        LogEntry.objects.log_action(self.simple_page, 'test')

        entries = LogEntry.objects.get_for_model(SimplePage)
        self.assertEqual(entries.count(), 2)
        self.assertListEqual(
            list(entries),
            list(LogEntry.objects.filter(object_id=str(self.simple_page.id)))
        )

    def test_get_for_instance(self):
        LogEntry.objects.log_action(self.page, 'test')
        LogEntry.objects.log_action(self.simple_page, 'test')

        self.assertListEqual(
            list(LogEntry.objects.get_for_instance(self.simple_page)),
            list(LogEntry.objects.filter(object_id=str(self.simple_page.id)))
        )

    def test_get_for_user(self):
        self.assertEqual(LogEntry.objects.get_for_user(self.user).count(), 1)  # the create from setUp

    def test_get_pages(self):
        user_entry = LogEntry.objects.log_action(self.user, 'user action')
        self.assertNotIn(user_entry, LogEntry.objects.get_pages())


class TestAuditLog(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=1)

        self.home_page = self.root_page.add_child(
            instance=SimplePage(title="Homepage", slug="home2", content="hello")
        )

    def test_page_create(self):
        self.assertEqual(LogEntry.objects.count(), 1)  # homepage

        page = self.home_page.add_child(
            instance=SimplePage(title="Hello", slug="my-page", content="world")
        )
        self.assertEqual(LogEntry.objects.count(), 2)
        log_entry = LogEntry.objects.order_by('pk').last()
        self.assertEqual(log_entry.action, 'wagtail.create')
        self.assertEqual(log_entry.object_id, str(page.id))
        self.assertEqual(log_entry.content_type, page.content_type)
        self.assertEqual(log_entry.object_title, page.get_admin_display_title())

    def test_page_edit(self):
        # Directly saving a revision should not yield a log entry
        self.home_page.save_revision()
        self.assertEqual(LogEntry.objects.count(), 1)

        # Explicitly ask to record the revision change
        self.home_page.save_revision(log_action=True)
        self.assertEqual(LogEntry.objects.count(), 2)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.create').count(), 1)

        # passing a string for the action should log this.
        self.home_page.save_revision(log_action='wagtail.custom_action')
        self.assertEqual(LogEntry.objects.filter(action='wagtail.custom_action').count(), 1)

    def test_page_publish(self):
        revision = self.home_page.save_revision()
        revision.publish()
        self.assertEqual(LogEntry.objects.count(), 2)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.publish').count(), 1)

    def test_page_unpublish(self):
        self.home_page.unpublish()
        self.assertEqual(LogEntry.objects.count(), 2)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.unpublish').count(), 1)

    def test_revision_revert(self):
        revision1 = self.home_page.save_revision()
        self.home_page.save_revision()

        self.home_page.save_revision(log_action=True, previous_revision=revision1)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.revert').count(), 1)

    def test_revision_schedule_publish(self):
        go_live_at = timezone.make_aware(datetime.now() + timedelta(days=1))
        self.home_page.go_live_at = go_live_at

        # with no live revision
        revision = self.home_page.save_revision()
        revision.publish()

        log_entries = LogEntry.objects.filter(action='wagtail.schedule.publish')
        self.assertEqual(log_entries.count(), 1)
        self.assertEqual(log_entries[0].data['revision']['id'], revision.id)
        self.assertEqual(log_entries[0].data['revision']['go_live_at'], go_live_at.strftime("%d %b %Y %H:%M"))

    def test_revision_schedule_revert(self):
        revision1 = self.home_page.save_revision()
        self.home_page.save_revision()

        self.home_page.go_live_at = timezone.make_aware(datetime.now() + timedelta(days=1))
        schedule_revision = self.home_page.save_revision()
        schedule_revision.publish(previous_revision=revision1)

        self.assertEqual(LogEntry.objects.filter(action='wagtail.schedule.revert').count(), 1)

    def test_revision_cancel_schedule(self):
        self.home_page.go_live_at = timezone.make_aware(datetime.now() + timedelta(days=1))
        revision = self.home_page.save_revision()
        revision.publish()

        revision.approved_go_live_at = None
        revision.save(update_fields=['approved_go_live_at'])

        self.assertEqual(LogEntry.objects.filter(action='wagtail.schedule.cancel').count(), 1)

    def test_page_lock_unlock(self):
        self.home_page.save(log_action='wagtail.lock')
        self.home_page.save(log_action='wagtail.unlock')

        self.assertEqual(LogEntry.objects.filter(action__in=['wagtail.lock', 'wagtail.unlock']).count(), 2)

    def test_page_copy(self):
        self.home_page.copy(update_attrs={'title': "About us", 'slug': 'about-us'})
        self.assertEqual(LogEntry.objects.filter(action='wagtail.copy').count(), 1)

    def test_page_move(self):
        section = self.root_page.add_child(
            instance=SimplePage(title="About us", slug="about", content="hello")
        )

        section.move(self.home_page)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.move').count(), 1)

    def test_page_delete(self):
        self.home_page.delete()
        self.assertEqual(LogEntry.objects.filter(action='wagtail.delete').count(), 1)

    def _create_workflow_and_tasks(self):
        workflow = Workflow.objects.create(name='test_workflow')
        task_1 = Task.objects.create(name='test_task_1')
        task_2 = Task.objects.create(name='test_task_2')
        WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
        WorkflowTask.objects.create(workflow=workflow, task=task_2, sort_order=2)
        return workflow, task_1, task_2

    def test_workflow_actions(self):
        workflow, _, _ = self._create_workflow_and_tasks()
        self.home_page.save_revision()
        user = get_user_model().objects.first()
        workflow_state = workflow.start(self.home_page, user)

        workflow_entry = LogEntry.objects.filter(action='wagtail.workflow.start')
        self.assertEqual(workflow_entry.count(), 1)
        self.assertEqual(workflow_entry[0].data, {
            'workflow': {
                'id': workflow.id,
                'title': workflow.name,
                'status': workflow_state.status,
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

                entry = LogEntry.objects.filter(action='wagtail.workflow.{}'.format(action))
                self.assertEqual(entry.count(), 1)
                self.assertEqual(entry[0].data, {
                    'workflow': {
                        'id': workflow.id,
                        'title': workflow.name,
                        'status': task_state.status,
                        'task': {
                            'id': task_state.task.id,
                            'title': task_state.task.name,
                        },
                        'next': {
                            'id': workflow_state.current_task_state.task.id,
                            'title': workflow_state.current_task_state.task.name,
                        },
                    }
                })

    def test_page_privacy(self):
        restriction = PageViewRestriction.objects.create(page=self.home_page)
        self.assertEqual(LogEntry.objects.filter(action='wagtail.view_restriction.create').count(), 1)
        restriction.restriction_type = PageViewRestriction.PASSWORD
        restriction.save()
        self.assertEqual(LogEntry.objects.filter(action='wagtail.view_restriction.edit').count(), 1)
