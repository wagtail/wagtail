from datetime import timedelta

from django.test import TestCase
from django.core import management
from django.utils import timezone
from django.utils.six import StringIO
from django.db import models

from wagtail.wagtailcore.models import Page, PageRevision
from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.tests.testapp.models import SimplePage, EventPage


class TestFixTreeCommand(TestCase):
    fixtures = ['test.json']

    def badly_delete_page(self, page):
        # Deletes a page the wrong way.
        # This will not update numchild and may leave orphans
        models.Model.delete(page)

    def run_command(self, **options):
        options.setdefault('interactive', False)

        output = StringIO()
        management.call_command('fixtree', stdout=output, **options)
        output.seek(0)

        return output

    def test_fixes_numchild(self):
        # Get homepage and save old value
        homepage = Page.objects.get(url_path='/home/')
        old_numchild = homepage.numchild

        # Break it
        homepage.numchild = 12345
        homepage.save()

        # Check that its broken
        self.assertEqual(Page.objects.get(url_path='/home/').numchild, 12345)

        # Call command
        self.run_command()

        # Check if its fixed
        self.assertEqual(Page.objects.get(url_path='/home/').numchild, old_numchild)

    def test_fixes_depth(self):
        # Get homepage and save old value
        homepage = Page.objects.get(url_path='/home/')
        old_depth = homepage.depth

        # Break it
        homepage.depth = 12345
        homepage.save()

        # Check that its broken
        self.assertEqual(Page.objects.get(url_path='/home/').depth, 12345)

        # Call command
        self.run_command()

        # Check if its fixed
        self.assertEqual(Page.objects.get(url_path='/home/').depth, old_depth)

    def test_detects_orphans(self):
        events_index = Page.objects.get(url_path='/home/events/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

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
        events_index = Page.objects.get(url_path='/home/events/')
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')

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


class TestMovePagesCommand(TestCase):
    fixtures = ['test.json']

    def run_command(self, from_, to):
        management.call_command('move_pages', str(from_), str(to), interactive=False, stdout=StringIO())

    def test_move_pages(self):
        # Get pages
        events_index = Page.objects.get(url_path='/home/events/')
        about_us = Page.objects.get(url_path='/home/about-us/')
        page_ids = events_index.get_children().values_list('id', flat=True)

        # Move all events into "about us"
        self.run_command(events_index.id, about_us.id)

        # Check that all pages moved
        for page_id in page_ids:
            self.assertEqual(Page.objects.get(id=page_id).get_parent(), about_us)


class TestReplaceTextCommand(TestCase):
    fixtures = ['test.json']

    def run_command(self, from_text, to_text):
        management.call_command('replace_text', from_text, to_text, interactive=False, stdout=StringIO())

    def test_replace_text(self):
        # Check that the christmas page is definitely about christmas
        christmas_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(christmas_page.title, "Christmas")
        self.assertEqual(christmas_page.speakers.first().last_name, "Christmas")
        self.assertEqual(christmas_page.advert_placements.first().colour, "greener than a Christmas tree")

        # Make it about easter
        self.run_command("Christmas", "Easter")

        # Check that it's now about easter
        easter_page = EventPage.objects.get(url_path='/home/events/christmas/')
        self.assertEqual(easter_page.title, "Easter")

        # Check that we also update the child objects (including advert_placements, which is defined on the superclass)
        self.assertEqual(easter_page.speakers.first().last_name, "Easter")
        self.assertEqual(easter_page.advert_placements.first().colour, "greener than a Easter tree")


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
            live=False,
            has_unpublished_changes=True,
            go_live_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(p.live)
        self.assertTrue(PageRevision.objects.filter(page=p).exclude(approved_go_live_at__isnull=True).exists())

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)
        self.assertTrue(p.first_published_at)
        self.assertFalse(p.has_unpublished_changes)
        self.assertFalse(PageRevision.objects.filter(page=p).exclude(approved_go_live_at__isnull=True).exists())

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

    def test_go_live_when_newer_revision_exists(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            live=False,
            has_unpublished_changes=True,
            go_live_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        page.title = "Goodbye world!"
        page.save_revision(submitted_for_moderation=False)

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)
        self.assertTrue(p.has_unpublished_changes)
        self.assertEqual(p.title, "Hello world!")

    def test_future_go_live_page_will_not_be_published(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            live=False,
            go_live_at=timezone.now() + timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(approved_go_live_at=timezone.now() - timedelta(days=1))

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(p.live)
        self.assertTrue(PageRevision.objects.filter(page=p).exclude(approved_go_live_at__isnull=True).exists())

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(p.live)
        self.assertTrue(PageRevision.objects.filter(page=p).exclude(approved_go_live_at__isnull=True).exists())

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
            live=True,
            has_unpublished_changes=False,
            expire_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
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
            live=True,
            expire_at=timezone.now() + timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)
        self.assertFalse(p.expired)

    def test_expired_pages_are_dropped_from_mod_queue(self):
        page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            live=False,
            expire_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        page.save_revision(submitted_for_moderation=True)

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(p.live)
        self.assertTrue(PageRevision.objects.filter(page=p, submitted_for_moderation=True).exists())

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(PageRevision.objects.filter(page=p, submitted_for_moderation=True).exists())
