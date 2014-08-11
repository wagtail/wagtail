from django.core.management.base import NoArgsCommand
from django.core.exceptions import ObjectDoesNotExist

from wagtail.wagtailcore.models import Page


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        problems_found = False

        for page in Page.objects.all():
            try:
                page.specific
            except ObjectDoesNotExist:
                self.stdout.write("Page %d (%s) is missing a subclass record; deleting." % (page.id, page.title))
                problems_found = True
                page.delete()

        (_, _, _, bad_depth, bad_numchild) = Page.find_problems()
        if bad_depth:
            self.stdout.write("Incorrect depth value found for pages: %r" % bad_depth)
        if bad_numchild:
            self.stdout.write("Incorrect numchild value found for pages: %r" % bad_numchild)

        if bad_depth or bad_numchild:
            Page.fix_tree(destructive=False)
            problems_found = True

        remaining_problems = Page.find_problems()
        if any(remaining_problems):
            self.stdout.write("Remaining problems (cannot fix automatically):")
            (bad_alpha, bad_path, orphans, bad_depth, bad_numchild) = remaining_problems
            if bad_alpha:
                self.stdout.write("Invalid characters found in path for pages: %r" % bad_alpha)
            if bad_path:
                self.stdout.write("Invalid path length found for pages: %r" % bad_path)
            if orphans:
                self.stdout.write("Orphaned pages found: %r" % orphans)
            if bad_depth:
                self.stdout.write("Incorrect depth value found for pages: %r" % bad_depth)
            if bad_numchild:
                self.stdout.write("Incorrect numchild value found for pages: %r" % bad_numchild)

        elif problems_found:
            self.stdout.write("All problems fixed.")
        else:
            self.stdout.write("No problems found.")
