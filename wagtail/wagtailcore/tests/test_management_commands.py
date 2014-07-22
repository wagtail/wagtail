from datetime import timedelta

from six import StringIO

from django.test import TestCase
from django.core import management
from django.utils import timezone

from wagtail.wagtailcore.models import Page, PageRevision
from wagtail.wagtailcore.signals import page_published, page_unpublished
from wagtail.tests.models import SimplePage


class TestFixTreeCommand(TestCase):
    fixtures = ['test.json']

    def run_command(self):
        management.call_command('fixtree', interactive=False, stdout=StringIO())

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
        self.assertEqual(Page.objects.get(url_path='/home/events/christmas/').title, "Christmas")

        # Make it about easter
        self.run_command("Christmas", "Easter")

        # Check that its now about easter
        self.assertEqual(Page.objects.get(url_path='/home/events/christmas/').title, "Easter")


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
        self.assertFalse(PageRevision.objects.filter(page=p).exclude(approved_go_live_at__isnull=True).exists())

        # Check that the page_published signal was fired
        self.assertTrue(signal_fired[0])
        self.assertEqual(signal_page[0], page)
        self.assertEqual(signal_page[0], signal_page[0].specific)

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
            expire_at=timezone.now() - timedelta(days=1),
        )
        self.root_page.add_child(instance=page)

        p = Page.objects.get(slug='hello-world')
        self.assertTrue(p.live)

        management.call_command('publish_scheduled_pages')

        p = Page.objects.get(slug='hello-world')
        self.assertFalse(p.live)
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
