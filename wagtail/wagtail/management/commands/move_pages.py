from django.core.management.base import BaseCommand

from wagtail.models import Page


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("from_id", type=int)
        parser.add_argument("to_id", type=int)

    def handle(self, *args, **options):
        # Get pages
        from_page = Page.objects.get(pk=options["from_id"])
        to_page = Page.objects.get(pk=options["to_id"])
        pages = from_page.get_children()

        # Move the pages
        self.stdout.write(
            "Moving "
            + str(len(pages))
            + ' pages from "'
            + from_page.title
            + '" to "'
            + to_page.title
            + '"'
        )
        for page in pages:
            page.move(to_page, pos="last-child")

        self.stdout.write("Done")
