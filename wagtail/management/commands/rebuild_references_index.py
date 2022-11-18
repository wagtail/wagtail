from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from wagtail.models import ReferenceIndex

DEFAULT_CHUNK_SIZE = 1000


class Command(BaseCommand):
    def write(self, *args, **kwargs):
        """
        Helper function that writes based on verbosity parameter

        """

        if self.verbosity != 0:
            self.stdout.write(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            "--chunk_size",
            action="store",
            dest="chunk_size",
            default=DEFAULT_CHUNK_SIZE,
            type=int,
            help="Set number of records to be fetched at once for inserting into the index",
        )

    def handle(self, **options):
        self.verbosity = options["verbosity"]

        chunk_size = options.get("chunk_size")
        object_count = 0

        self.write("Rebuilding reference index")

        with transaction.atomic():
            ReferenceIndex.objects.all().delete()

            for model in apps.get_models():
                if not ReferenceIndex.model_is_indexable(model):
                    continue

                self.write(str(model))

                # Add items (chunk_size at a time)
                for chunk in self.print_iter_progress(
                    self.queryset_chunks(model.objects.all().order_by("pk"), chunk_size)
                ):
                    for instance in chunk:
                        ReferenceIndex.create_or_update_for_object(instance)

                    object_count += len(chunk)

                self.print_newline()

        self.write("Indexed %d objects" % object_count)
        self.print_newline()

    def print_newline(self):
        self.write("")

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
            self.write(".", ending="")
            if i % 40 == 0:
                self.print_newline()
                self.write(" " * 35, ending="")

            elif i % 10 == 0:
                self.write(" ", ending="")

            self.stdout.flush()

    # Atomic so the count of models doesn't change as it is iterated
    @transaction.atomic
    def queryset_chunks(self, qs, chunk_size=DEFAULT_CHUNK_SIZE):
        """
        Yield a queryset in chunks of at most ``chunk_size``. The chunk yielded
        will be a list, not a queryset. Iterating over the chunks is done in a
        transaction so that the order and count of items in the queryset
        remains stable.
        """
        i = 0
        while True:
            items = list(qs[i * chunk_size :][:chunk_size])
            if not items:
                break
            yield items
            i += 1
