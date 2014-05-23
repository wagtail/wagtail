from __future__ import print_function

from django.core.management.base import BaseCommand

from wagtail.wagtailcore.models import Page


class Command(BaseCommand):
    def handle(self, _from_id, _to_id, **options):
        # Convert args to integers
        from_id = int(_from_id)
        to_id = int(_to_id)

        # Get pages
        from_page = Page.objects.get(pk=from_id)
        to_page = Page.objects.get(pk=to_id)
        pages = from_page.get_children()

        # Move the pages
        print('Moving ' + str(len(pages)) + ' pages from "' + from_page.title + '" to "' + to_page.title + '"')
        for page in pages:
            page.move(to_page, pos='last-child')

        print('Done')
