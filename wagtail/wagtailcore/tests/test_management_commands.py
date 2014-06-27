from StringIO import StringIO

from django.test import TestCase, Client
from django.http import HttpRequest, Http404
from django.core import management
from django.contrib.auth.models import User

from wagtail.wagtailcore.models import Page, Site, UserPagePermissionsProxy
from wagtail.tests.models import EventPage, EventIndex, SimplePage


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
