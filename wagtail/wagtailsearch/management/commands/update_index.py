from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from wagtail.wagtailsearch.index import get_indexed_models
from wagtail.wagtailsearch.backends import get_search_backend


INDENT = ' ' * 8


class Command(BaseCommand):
    def get_object_list(self):
        # Return list of (model_name, queryset) tuples
        return [
            (model, model.get_indexed_objects())
            for model in get_indexed_models()
        ]

    def update_backend(self, backend_name, object_list):
        # Print info
        self.stdout.write("Updating backend: " + backend_name)

        # Get backend
        backend = get_search_backend(backend_name)

        # Get rebuilder
        rebuilder = backend.get_rebuilder()

        if not rebuilder:
            self.stdout.write(backend_name + ": Backend doesn't support rebuild. Skipping")
            return

        # Start rebuild
        self.stdout.write(backend_name + ": Starting rebuild")
        rebuilder.start()

        for model, queryset in object_list:
            self.stdout.write(backend_name + ": Indexing model '%s.%s'" % (
                model._meta.app_label,
                model.__name__,
            ))

            # Add model
            rebuilder.add_model(model)

            # Add items (1000 at a time)
            count = 0
            for chunk in self.progress(self.queryset_chunks(queryset)):
                rebuilder.add_items(model, chunk)
                count += len(chunk)

            self.stdout.write(INDENT + "Indexed %d %s" % (
                count, model._meta.verbose_name_plural))

        # Finish rebuild
        self.stdout.write(backend_name + ": Finishing rebuild")
        rebuilder.finish()

    option_list = BaseCommand.option_list + (
        make_option('--backend',
            action='store',
            dest='backend_name',
            default=None,
            help="Specify a backend to update",
        ),
    )

    def handle(self, **options):
        # Get object list
        object_list = self.get_object_list()

        # Get list of backends to index
        if options['backend_name']:
            # index only the passed backend
            backend_names = [options['backend_name']]
        elif hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
            # index all backends listed in settings
            backend_names = settings.WAGTAILSEARCH_BACKENDS.keys()
        else:
            # index the 'default' backend only
            backend_names = ['default']

        # Update backends
        for backend_name in backend_names:
            self.update_backend(backend_name, object_list)

    def progress(self, iterable, gap=10, new_line=5, indent=INDENT):
        """
        Print a progress meter while iterating over an iterable. Use it as part
        of a ``for`` loop::

            for item in self.progress(big_long_list):
                self.do_expensive_computation(item)

        A ``.`` character is printed for every value in the iterable,
        a space every ``gap`` items, and a new line every ``new_line`` gaps.
        Each line of output is prefixed with ``indent``
        """
        self.stdout.write(indent, ending='')
        for i, value in enumerate(iterable, start=1):
            yield value
            self.stdout.write('.', ending='')
            if i % (gap * new_line) == 0:
                self.stdout.write('')
                self.stdout.write(indent, ending='')
            elif i % gap == 0:
                self.stdout.write(' ', ending='')
            self.stdout.flush()
        self.stdout.write('')

    # Atomic so the count of models doesnt change as it is iterated
    @transaction.atomic
    def queryset_chunks(self, qs, chunk_size=1000):
        """
        Yield a queryset in chunks of at most ``chunk_size``. The chunk yeilded
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
