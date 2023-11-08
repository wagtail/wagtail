import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from wagtail.images import get_image_model

logger = logging.getLogger(__name__)


def progress_bar(current, total, bar_length=50):
    fraction = current / total

    arrow = int(fraction * bar_length - 1) * "-" + ">"
    padding = int(bar_length - len(arrow)) * " "

    ending = "\n" if current == total else "\r"

    return (f"Progress: [{arrow}{padding}] {int(fraction*100)}%", ending)


class Command(BaseCommand):
    """Command to create missing image renditions with the option to remove (purge) any existing ones."""

    help = "This command will generate all image renditions, with an option to purge existing renditions first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge-only",
            action="store_true",
            help="Purge all image renditions without regenerating them",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=50,
            help="Operate in x size chunks (default: %(default)s)",
        )

    def handle(self, *args, **options):
        Rendition = get_image_model().get_rendition_model()

        renditions = Rendition.objects.all()

        purge_only = options["purge_only"]

        if not renditions.exists():
            self.stdout.write(self.style.WARNING("No image renditions found."))
            return

        rendition_ids = list(renditions.values_list("id", flat=True))
        num_renditions = len(rendition_ids)

        if purge_only:
            self.stdout.write(
                self.style.HTTP_INFO(f"Purging {num_renditions} rendition(s)")
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(f"Regenerating {num_renditions} rendition(s)")
            )

        progress_bar_current = 1
        for rendition in (
            # Pre-calculate the ids of the renditions to change,
            # otherwise `.iterator` never ends.
            renditions.filter(id__in=rendition_ids)
            .select_related("image")
            .iterator(chunk_size=options["chunk_size"])
        ):
            try:
                with transaction.atomic():
                    rendition_filter = rendition.filter
                    rendition_image = rendition.image

                    # Delete the existing rendition
                    rendition.delete()

                    _progress_bar = progress_bar(progress_bar_current, num_renditions)
                    self.stdout.write(_progress_bar[0], ending=_progress_bar[1])
                    progress_bar_current = progress_bar_current + 1

                    if not purge_only:
                        # Create a new one
                        rendition_image.get_rendition(rendition_filter)
            except:  # noqa:E722
                logger.exception("Error operating on rendition %d", rendition.id)
                self.stderr.write(
                    self.style.ERROR(f"Failed to operate on rendition {rendition.id}")
                )
                num_renditions -= 1

        if num_renditions:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully processed {num_renditions} rendition(s)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("Could not process any renditions."))
