from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from wagtail.wagtailcore.models import Page


class Command(BaseCommand):
    args = "<from id> <to id>"

    def handle(self, _from_id, _to_id, **options):
        # Convert args to integers
        from_id = int(_from_id)
        to_id = int(_to_id)

        # Get pages
        from_page = Page.objects.get(pk=from_id)
        to_page = Page.objects.get(pk=to_id)
        pages = from_page.get_children()

        # Move the pages
        self.stdout.write(
            'Moving ' + str(len(pages)) + ' pages from "' + from_page.title + '" to "' + to_page.title + '"'
        )
        for page in pages:
            page.move(to_page, pos='last-child')

        self.stdout.write('Done')
