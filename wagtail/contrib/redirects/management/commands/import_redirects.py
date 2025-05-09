import os

from django.core.management.base import BaseCommand

from wagtail.contrib.redirects.base_formats import Dataset
from wagtail.contrib.redirects.forms import RedirectForm
from wagtail.contrib.redirects.utils import (
    get_format_cls_by_extension,
    get_supported_extensions,
)
from wagtail.models import Site


class Command(BaseCommand):
    help = "Imports redirects from a .csv, .tsv or .xlsx file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            help="Path to file",
            type=str,
            required=True,
        )
        parser.add_argument(
            "--site",
            help="The site where redirects will be associated",
            type=int,
        )
        parser.add_argument(
            "--permanent",
            help="Save redirects as permanent redirects",
            type=bool,
            default=True,
        )
        parser.add_argument(
            "--from",
            help="The column where to read from link",
            default=0,
            type=int,
        )
        parser.add_argument(
            "--to",
            help="The column where to read to link",
            default=1,
            type=int,
        )
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Run only in test mode, will not create redirects",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run only in test mode, will not create redirects",
        )
        parser.add_argument(
            "--ask",
            help="Ask before creating",
            action="store_true",
        )
        parser.add_argument(
            "--format",
            help="Source file format (csv, tsv or xlsx)",
            choices=get_supported_extensions(),
            type=str,
        )
        parser.add_argument(
            "--offset", help="Import starting with index", type=int, default=None
        )
        parser.add_argument(
            "--limit", help="Limit import to num items", type=int, default=None
        )

    def handle(self, *args, **options):
        src = options["src"]
        from_index = options.pop("from")
        to_index = options.pop("to")
        site_id = options.pop("site", None)
        permanent = options.pop("permanent")

        dry_run = options.pop("dry_run", False) or options.pop("dry-run", False)
        format_ = options.pop("format", None)
        ask = options.pop("ask")
        offset = options.pop("offset")
        limit = options.pop("limit")

        errors = []
        successes = 0
        skipped = 0
        total = 0
        site = None

        if site_id:
            site = Site.objects.get(id=site_id)

        if not os.path.exists(src):
            raise Exception(f"Missing file '{src}'")

        if not os.path.getsize(src) > 0:
            raise Exception(f"File '{src}' is empty")

        _, extension = os.path.splitext(src)
        extension = extension.lstrip(".")

        if not format_:
            format_ = extension

        import_format_cls = get_format_cls_by_extension(format_)
        if import_format_cls is None:
            raise Exception(f"Invalid format '{extension}'")
        input_format = import_format_cls()

        if extension in ["xls", "xlsx"]:
            mode = "rb"
        else:
            mode = "r"

        with open(src, mode) as fh:
            imported_data = input_format.create_dataset(fh.read())
            sample_data = Dataset(imported_data[:4], imported_data.headers)

            self.stdout.write("Sample data:")
            self.stdout.write(str(sample_data))

            self.stdout.write("--------------")

            if site:
                self.stdout.write(f"Using site: {site.hostname}")

            self.stdout.write("Importing redirects:")

            if offset:
                imported_data = imported_data[offset:]
            if limit:
                imported_data = imported_data[:limit]

            for row in imported_data:
                total += 1

                from_link = row[from_index]
                to_link = row[to_index]

                data = {
                    "old_path": from_link,
                    "redirect_link": to_link,
                    "is_permanent": permanent,
                }

                if site:
                    data["site"] = site.pk

                form = RedirectForm(data)
                if not form.is_valid():
                    error = form.errors.as_text().replace("\n", "")
                    self.stdout.write(
                        "{}. Error: {} -> {} (Reason: {})".format(
                            total,
                            from_link,
                            to_link,
                            error,
                        )
                    )
                    errors.append(error)
                    continue

                if ask:
                    answer = get_input(
                        "{}. Found {} -> {} Create? y/N: ".format(
                            total,
                            from_link,
                            to_link,
                        )
                    )

                    if not answer.lower().startswith("y"):
                        skipped += 1
                        continue
                else:
                    self.stdout.write(
                        "{}. {} -> {}".format(
                            total,
                            from_link,
                            to_link,
                        )
                    )

                if dry_run:
                    successes += 1
                    continue

                form.save()
                successes += 1

        self.stdout.write("\n")
        self.stdout.write(f"Found: {total}")
        self.stdout.write(f"Created: {successes}")
        self.stdout.write(f"Skipped : {skipped}")
        self.stdout.write(f"Errors: {len(errors)}")


def get_input(msg):  # pragma: no cover
    return input(msg)
