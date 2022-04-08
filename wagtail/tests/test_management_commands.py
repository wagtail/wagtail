from datetime import timedelta
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import management
from django.db import models
from django.test import TestCase
from django.utils import timezone

from wagtail.models import Collection, Page, PageLogEntry, PageRevision
from wagtail.signals import page_published, page_unpublished
from wagtail.test.testapp.models import EventPage, SecretPage, SimplePage


class TestFixTreeCommand(TestCase):
    fixtures = ["test.json"]

    def badly_delete_page(self, page):
        # Deletes a page the wrong way.
        # This will not update numchild and may leave orphans
        models.Model.delete(page)

    def run_command(self, **options):
        options.setdefault("interactive", False)

        output = StringIO()
        management.call_command("fixtree", stdout=output, **options)
        output.seek(0)

        return output

    def test_fixes_numchild(self):
        # Get homepage and save old value
        homepage = Page.objects.get(url_path="/home/")
        old_numchild = homepage.numchild

        # Break it
        homepage.numchild = 12345
        homepage.save()

        # Check that its broken
        self.assertEqual(Page.objects.get(url_path="/home/").numchild, 12345)

        # Call command
        self.run_command()

        # Check if its fixed
        self.assertEqual(Page.objects.get(url_path="/home/").numchild, old_numchild)

    def test_fixes_depth(self):
        # Get homepage and save old value
        homepage = Page.objects.get(url_path="/home/")
        old_depth = homepage.depth

        # Break it
        homepage.depth = 12345
        homepage.save()

        # also break the root collection's depth
        root_collection = Collection.get_first_root_node()
        root_collection.depth = 42
        root_collection.save()

        # Check that its broken
        self.assertEqual(Page.objects.get(url_path="/home/").depth, 12345)
        self.assertEqual(Collection.objects.get(id=root_collection.id).depth, 42)

        # Call command
        self.run_command()

        # Check if its fixed
        self.assertEqual(Page.objects.get(url_path="/home/").depth, old_depth)
        self.assertEqual(Collection.objects.get(id=root_collection.id).depth, 1)

    def test_detects_orphans(self):
        events_index = Page.objects.get(url_path="/home/events/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # Delete the events index badly
        self.badly_delete_page(events_index)

        # Check that christmas_page is still in the tree
        self.assertTrue(Page.objects.filter(id=christmas_page.id).exists())

        # Call command
        output = self.run_command()

        # Check that the issues were detected
        output_string = output.read()
        self.assertIn("Incorrect numchild value found for pages: [2]", output_string)
        # Note that page ID 15 was also deleted, but is not picked up here, as
        # it is a child of 14.
        self.assertIn("Orphaned pages found: [4, 5, 6, 9, 13, 15]", output_string)

        # Check that christmas_page is still in the tree
        self.assertTrue(Page.objects.filter(id=christmas_page.id).exists())

    def test_deletes_orphans(self):
        events_index = Page.objects.get(url_path="/home/events/")
        christmas_page = EventPage.objects.get(url_path="/home/events/christmas/")

        # Delete the events index badly
        self.badly_delete_page(events_index)

        # Check that christmas_page is still in the tree
        self.assertTrue(Page.objects.filter(id=christmas_page.id).exists())

        # Call command
        # delete_orphans simulates a user pressing "y" at the prompt
        output = self.run_command(delete_orphans=True)

        # Check that the issues were detected
        output_string = output.read()
        self.assertIn("Incorrect numchild value found for pages: [2]", output_string)
        self.assertIn("7 orphaned pages deleted.", output_string)

        # Check that christmas_page has been deleted
        self.assertFalse(Page.objects.filter(id=christmas_page.id).exists())

    def test_remove_path_holes(self):
        events_index = Page.objects.get(url_path="/home/events/")
        # Delete the event page in path position 0001
        Page.objects.get(path=events_index.path + "0001").delete()

        self.run_command(full=True)
        # the gap at position 0001 should have been closed
        events_index = Page.objects.get(url_path="/home/events/")
        self.assertTrue(Page.objects.filter(path=events_index.path + "0001").exists())


class TestMovePagesCommand(TestCase):
    fixtures = ["test.json"]

    def run_command(self, from_, to):
        management.call_command("move_pages", str(from_), str(to), stdout=StringIO())

    def test_move_pages(self):
        # Get pages
        events_index = Page.objects.get(url_path="/home/events/")
        about_us = Page.objects.get(url_path="/home/about-us/")
        page_ids = events_index.get_children().values_list("id", flat=True)

        # Move all events into "about us"
        self.run_command(events_index.id, about_us.id)

        # Check that all pages moved
        for page_id in page_ids:
            self.assertEqual(Page.objects.get(id=page_id).get_parent(), about_us)


class TestSetUrlPathsCommand(TestCase):

    fixtures = ["test.json"]

    def run_command(self):
        management.call_command("set_url_paths", stdout=StringIO())

    def test_set_url_paths(self):
        self.run_command()


class TestPublishScheduledPagesCommand(TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

    def test_go_live_page_will_be_published(self):
        # Connect a mock signal handler to page_published signal
        signal_fired = [False]
        signal_page = [None]

        def page_published_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance

        page_published.connect(page_published_handler)

        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
            go_live_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(p.live)
        self.assertTrue(
            PageRevision.objects.filter(page=p)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertTrue(p.live)
        self.assertTrue(p.first_published_at)
        self.assertFalse(p.has_unpublished_changes)
        self.assertFalse(
            PageRevision.objects.filter(page=p)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_go_live_when_newer_revision_exists(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            has_unpublished_changes=True,
            go_live_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        page.title = "Goodbye world!"
        page.save_revision(submitted_for_moderation=False)

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertTrue(p.live)
        self.assertTrue(p.has_unpublished_changes)
        self.assertEqual(p.title, "Hello world!")

    def test_future_go_live_page_will_not_be_published(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            go_live_at=timezone.now() + timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(p.live)
        self.assertTrue(
            PageRevision.objects.filter(page=p)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(p.live)
        self.assertTrue(
            PageRevision.objects.filter(page=p)
            .exclude(approved_go_live_at__isnull=True)
            .exists()
        )

    def test_expired_page_will_be_unpublished(self):
        # Connect a mock signal handler to page_unpublished signal
        signal_fired = [False]
        signal_page = [None]

        def page_unpublished_handler(sender, instance, **kwargs):
            signal_fired[0] = True
            signal_page[0] = instance

        page_unpublished.connect(page_unpublished_handler)

        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=True,
            has_unpublished_changes=False,
            expire_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        p = Page.objects.get(slug="hello-world")
        self.assertTrue(p.live)

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(p.live)
        self.assertTrue(p.has_unpublished_changes)
        self.assertTrue(p.expired)

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_future_expired_page_will_not_be_unpublished(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=True,
            expire_at=timezone.now() + timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        p = Page.objects.get(slug="hello-world")
        self.assertTrue(p.live)

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertTrue(p.live)
        self.assertFalse(p.expired)

    def test_expired_pages_are_dropped_from_mod_queue(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            expire_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(submitted_for_moderation=True)

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(p.live)
        self.assertTrue(
            PageRevision.objects.filter(page=p, submitted_for_moderation=True).exists()
        )

        management.call_command("publish_scheduled_pages")

        p = Page.objects.get(slug="hello-world")
        self.assertFalse(
            PageRevision.objects.filter(page=p, submitted_for_moderation=True).exists()
        )


class TestPurgeRevisionsCommand(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
        )
        self.root_page.add_child(instance=self.page)
        self.page.refresh_from_db()

    def run_command(self, days=None):
        if days:
            days_input = "--days=" + str(days)
            return management.call_command(
                "purge_revisions", days_input, stdout=StringIO()
            )
        return management.call_command("purge_revisions", stdout=StringIO())

    def test_latest_revision_not_purged(self):

        revision_1 = self.page.save_revision()

        revision_2 = self.page.save_revision()

        self.run_command()

        # revision 1 should be deleted, revision 2 should not be
        self.assertNotIn(revision_1, PageRevision.objects.filter(page=self.page))
        self.assertIn(revision_2, PageRevision.objects.filter(page=self.page))

    def test_revisions_in_moderation_not_purged(self):

        self.page.save_revision(submitted_for_moderation=True)

        revision = self.page.save_revision()

        self.run_command()

        self.assertTrue(
            PageRevision.objects.filter(
                page=self.page, submitted_for_moderation=True
            ).exists()
        )

        try:
            from wagtail.models import Task, Workflow, WorkflowTask

            workflow = Workflow.objects.create(name="test_workflow")
            task_1 = Task.objects.create(name="test_task_1")
            user = get_user_model().objects.first()
            WorkflowTask.objects.create(workflow=workflow, task=task_1, sort_order=1)
            workflow.start(self.page, user)
            self.page.save_revision()
            self.run_command()
            # even though no longer the latest revision, the old revision should stay as it is
            # attached to an in progress workflow
            self.assertIn(revision, PageRevision.objects.filter(page=self.page))
        except ImportError:
            pass

    def test_revisions_with_approve_go_live_not_purged(self):

        approved_revision = self.page.save_revision(
            approved_go_live_at=timezone.now() + timedelta(days=1)
        )

        self.page.save_revision()

        self.run_command()

        self.assertIn(approved_revision, PageRevision.objects.filter(page=self.page))

    def test_purge_revisions_with_date_cutoff(self):

        old_revision = self.page.save_revision()

        self.page.save_revision()

        self.run_command(days=30)

        # revision should not be deleted, as it is younger than 30 days
        self.assertIn(old_revision, PageRevision.objects.filter(page=self.page))

        old_revision.created_at = timezone.now() - timedelta(days=31)
        old_revision.save()

        self.run_command(days=30)

        # revision is now older than 30 days, so should be deleted
        self.assertNotIn(old_revision, PageRevision.objects.filter(page=self.page))


class TestCreateLogEntriesFromRevisionsCommand(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
            live=False,
            expire_at=timezone.now() - timedelta(days=1),
        )

        Page.objects.get(id=2).add_child(instance=self.page)

        # Create empty revisions, which should not be converted to log entries
        for i in range(3):
            self.page.save_revision()

        # Add another revision with a content change
        self.page.title = "Hello world!!"
        revision = self.page.save_revision()
        revision.publish()

        # Do the same with a SecretPage (to check that the version comparison code doesn't
        # trip up on permission-dependent edit handlers)
        self.secret_page = SecretPage(
            title="The moon",
            slug="the-moon",
            boring_data="the moon",
            secret_data="is made of cheese",
            live=False,
        )

        Page.objects.get(id=2).add_child(instance=self.secret_page)

        # Create empty revisions, which should not be converted to log entries
        for i in range(3):
            self.secret_page.save_revision()

        # Add another revision with a content change
        self.secret_page.secret_data = "is flat"
        revision = self.secret_page.save_revision()
        revision.publish()

        # clean up log entries
        PageLogEntry.objects.all().delete()

    def test_log_entries_created_from_revisions(self):
        management.call_command("create_log_entries_from_revisions")

        # Should not create entries for empty revisions.
        self.assertListEqual(
            list(PageLogEntry.objects.values_list("action", flat=True)),
            [
                "wagtail.publish",
                "wagtail.edit",
                "wagtail.create",
                "wagtail.publish",
                "wagtail.edit",
                "wagtail.create",
            ],
        )

    def test_command_doesnt_crash_for_revisions_without_page_model(self):
        with mock.patch(
            "wagtail.models.ContentType.model_class",
            return_value=None,
        ):
            management.call_command("create_log_entries_from_revisions")
            self.assertEqual(PageLogEntry.objects.count(), 0)
