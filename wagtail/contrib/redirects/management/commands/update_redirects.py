from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page
from wagtail.models.sites import get_site_for_hostname


class Command(BaseCommand):
    help = "Converts target URLs to Wagtail pages, if they exist"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run only in test mode, will not update redirects",
        )

    def handle(self, *args, **options):
        dry_run = options.pop("dry_run", False)

        converted = 0
        skipped = 0
        total = 0

        for redirect in Redirect.objects.exclude(redirect_link=""):
            total += 1
            url = urlparse(redirect.redirect_link)
            hostname = url.hostname
            port = url.port or 80
            path = url.path
            site = get_site_for_hostname(hostname, port)
            if not path.endswith("/"):
                path = path + "/"

            if site:
                root_path = site.root_page.url_path
                full_path = root_path + path.lstrip("/")
                page = Page.objects.filter(url_path=full_path).live().first()
                if page:
                    if dry_run:
                        converted += 1
                        self.stdout.write(f"Would convert redirect {redirect.id}")
                        continue
                    redirect.redirect_page = page
                    redirect.redirect_link = ""
                    redirect.save()
                    converted += 1
                    self.stdout.write(f"Converted redirect {redirect.id}")
                else:
                    skipped += 1
                    self.stdout.write(
                        f"Skipping redirect {redirect.id} - no matching page found"
                    )
            else:
                skipped += 1
                self.stdout.write(
                    f"Skipping redirect {redirect.id} - no matching page found"
                )
        self.stdout.write(f"Total: {total}")
        self.stdout.write(f"Converted: {converted}")
        self.stdout.write(f"Skipped: {skipped}")
