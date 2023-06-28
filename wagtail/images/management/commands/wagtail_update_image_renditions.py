import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from wagtail.images import get_image_model

logger = logging.getLogger(__name__)


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
            self.stdout.write("No image renditions found.")
            return

        rendition_ids = list(renditions.values_list("id", flat=True))

        if purge_only:
            self.stdout.write(
                self.style.HTTP_INFO(f"Purging {len(rendition_ids)} rendition(s)")
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(f"Regenerating {len(rendition_ids)} rendition(s)")
            )

        for rendition in (
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

                    if not purge_only:
                        # Create a new one
                        rendition_image.get_rendition(rendition_filter)
            except:  # noqa:E722
                logger.exception("Error operating on rendition %d", rendition.id)
                self.stderr.write(
                    self.style.ERROR(f"Failed to operate on rendition {rendition.id}")
                )

        self.stdout.write(self.style.SUCCESS("Success"))
