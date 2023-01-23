from django.core.management.base import BaseCommand
from django.db import transaction

from wagtail.images import get_image_model


class Command(BaseCommand):
    """Command to create missing image renditions with the option to remove (purge) any existing ones."""

    help = "This command will generate all image renditions, with an option to purge existing renditions first."

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge-only",
            action="store_true",
            help="Purge all image renditions without regenerating them",
        )

    def handle(self, *args, **options):
        Rendition = get_image_model().get_rendition_model()

        renditions = Rendition.objects.all()

        if not renditions.exists():
            self.stdout.write("No image renditions found.")
            return

        if options["purge_only"]:
            rendition_count = renditions.count()
            renditions.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully purged {rendition_count} image rendition(s)"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(f"Regenerating {renditions.count()} rendition(s)")
            )
            # Pre-calculate the ids of the renditions to change, otherwise `.iterator` never
            # ends.
            rendition_ids = list(renditions.values_list("id", flat=True))

            for rendition in (
                renditions.filter(id__in=rendition_ids)
                .select_related("image")
                .iterator(chunk_size=10)
            ):
                with transaction.atomic():
                    rendition_filter = rendition.filter
                    rendition_image = rendition.image

                    # Delete the existing rendition
                    rendition.delete()

                    # Create a new one
                    rendition_image.get_rendition(rendition_filter)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully regenerated {len(rendition_ids)} image rendition(s)"
                )
            )
