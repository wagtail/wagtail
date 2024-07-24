from django.core.management.base import BaseCommand

from wagtail.embeds.models import Embed


class Command(BaseCommand):
    help = "Deletes all of the Embed model objects"

    def handle(self, *args, **options):
        embeds = Embed.objects.all()

        deleted_embeds_count = embeds.delete()[0]
        if deleted_embeds_count:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {deleted_embeds_count} embeds"
                )
            )
        else:
            self.stdout.write("Successfully deleted 0 embeds")
