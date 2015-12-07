from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from wagtail.wagtailsearch.index import get_indexed_models
from wagtail.wagtailsearch.backends import get_search_backend


class Command(BaseCommand):
    def get_object_list(self):
        # Return list of (model_name, queryset) tuples
        return [
            (model, model.get_indexed_objects())
            for model in get_indexed_models()
        ]

    def update_index(self, index_name, object_list):
        # Print info
        self.stdout.write("Updating index: " + index_name)

        # Get index
        index = get_search_backend(index_name)

        # Get rebuilder
        rebuilder = index.get_rebuilder()

        if not rebuilder:
            self.stdout.write(index_name + ": Backend doesn't support rebuild. Skipping")
            return

        # Start rebuild
        self.stdout.write(index_name + ": Starting rebuild")
        rebuilder.start()

        for model, queryset in object_list:
            self.stdout.write(index_name + ": Indexing model '%s.%s'" % (
                model._meta.app_label,
                model.__name__,
            ))

            # Add model
            rebuilder.add_model(model)

            # Add items (1000 at a time)
            count = 0
            for chunk in self.print_iter_progress(self.queryset_chunks(queryset)):
                rebuilder.add_items(model, chunk)
                count += len(chunk)

            self.stdout.write("Indexed %d %s" % (
                count, model._meta.verbose_name_plural))
            self.print_newline()

        # Finish rebuild
        self.stdout.write(index_name + ": Finishing rebuild")
        rebuilder.finish()

    option_list = BaseCommand.option_list + (
        make_option(
            '--backend',
            action='store',
            dest='index_name',
            default=None,
            help="Specify an index to update",
        ),
    )

    def handle(self, **options):
        # Get object list
        object_list = self.get_object_list()

        # Get list of indices to update
        if options['index_name']:
            # update only the passed index
            index_names = [options['index_name']]
        elif hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
            # update all indices listed in settings
            index_names = settings.WAGTAILSEARCH_BACKENDS.keys()
        else:
            # update the 'default' index only
            index_names = ['default']

        # Update indices
        for index_name in index_names:
            self.update_index(index_name, object_list)

    def print_newline(self):
        self.stdout.write('')

    def print_iter_progress(self, iterable):
        """
        Print a progress meter while iterating over an iterable. Use it as part
        of a ``for`` loop::

            for item in self.print_iter_progress(big_long_list):
                self.do_expensive_computation(item)

        A ``.`` character is printed for every value in the iterable,
        a space every 10 items, and a new line every 50 items.
        """
        for i, value in enumerate(iterable, start=1):
            yield value
            self.stdout.write('.', ending='')
            if i % 50 == 0:
                self.print_newline()

            elif i % 10 == 0:
                self.stdout.write(' ', ending='')

            self.stdout.flush()

        self.print_newline()

    # Atomic so the count of models doesnt change as it is iterated
    @transaction.atomic
    def queryset_chunks(self, qs, chunk_size=1000):
        """
        Yield a queryset in chunks of at most ``chunk_size``. The chunk yielded
        will be a list, not a queryset. Iterating over the chunks is done in a
        transaction so that the order and count of items in the queryset
        remains stable.
        """
        i = 0
        while True:
            items = list(qs[i * chunk_size:][:chunk_size])
            if not items:
                break
            yield items
            i += 1
