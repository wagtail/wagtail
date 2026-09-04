import re
import warnings
from io import StringIO

from django.core import management
from django.test import (
    TestCase,
    TransactionTestCase,
    override_settings,
    tag,
)

from wagtail.models import Collection

from ..management.commands.wagtail_update_image_renditions import progress_bar
from .utils import Image, get_test_image_file

# note .utils.Image already does get_image_model()
Rendition = Image.get_rendition_model()


class TestUpdateImageRenditions(TestCase):
    REAESC = re.compile(r"\x1b[^m]*m")

    @classmethod
    def setUpTestData(cls):
        cls.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_image.png", colour="white"),
        )

        cls.rendition = Rendition.objects.create(
            image=cls.image,
            filter_spec="original",
            width=1000,
            height=1000,
            file=get_test_image_file(
                filename="test_rendition.png", colour="white", size=(1000, 1000)
            ),
        )

    def delete_renditions(self):
        renditions = Rendition.objects.all()
        for rendition in renditions:
            try:
                rendition_image = rendition.image
                rendition.delete()
            except Exception:  # noqa: BLE001
                warnings.warn(f"Could not delete rendition for {rendition_image}")

    def run_command(self, **options):
        output = StringIO()
        management.call_command(
            "wagtail_update_image_renditions", stdout=output, **options
        )
        output.seek(0)

        return output

    def test_progress_bar(self):
        total_rendition = 10
        out = StringIO()
        for current in range(1, total_rendition + 1):
            progress_bar_output = progress_bar(current, total_rendition)[0]
            out.write(progress_bar_output)
        out.seek(0)
        expected_output = "".join(
            [
                "Progress: [---->                                             ] 10%",
                "Progress: [--------->                                        ] 20%",
                "Progress: [-------------->                                   ] 30%",
                "Progress: [------------------->                              ] 40%",
                "Progress: [------------------------>                         ] 50%",
                "Progress: [----------------------------->                    ] 60%",
                "Progress: [---------------------------------->               ] 70%",
                "Progress: [--------------------------------------->          ] 80%",
                "Progress: [-------------------------------------------->     ] 90%",
                "Progress: [------------------------------------------------->] 100%",
            ]
        )
        self.assertIn(expected_output, out.getvalue())

    def test_exits_early_for_no_renditions(self):
        self.delete_renditions()
        # checking when command is called without any arguments
        output = self.run_command()
        output_string = self.REAESC.sub("", output.read())
        self.assertEqual(output_string, "No image renditions found.\n")

        # checking when command is called with '--purge-only'
        output = self.run_command(purge_only=True)
        output_string = self.REAESC.sub("", output.read())
        self.assertEqual(output_string, "No image renditions found.\n")

    def test_image_renditions(self):
        renditions = Rendition.objects.all()
        total_renditions = len(renditions)
        output = self.run_command()
        output_string = self.REAESC.sub("", output.read())
        # checking if the number of renditions regenerated equal total_renditions
        self.assertEqual(
            output_string,
            f"Regenerating {total_renditions} rendition(s)\n"
            f"Progress: [------------------------------------------------->] 100%\n"
            f"Successfully processed {total_renditions} rendition(s)\n",
        )

        # checking if the number of renditions now equal total_renditions
        renditions_now = Rendition.objects.all()
        total_renditions_now = len(renditions_now)
        self.assertEqual(total_renditions_now, total_renditions)

    def test_image_renditions_with_purge_only(self):
        renditions = Rendition.objects.all()
        total_renditions = len(renditions)
        output = self.run_command(purge_only=True)
        output_string = self.REAESC.sub("", output.read())
        # checking if the number of renditions purged equal total_renditions
        self.assertEqual(
            output_string,
            f"Purging {total_renditions} rendition(s)\n"
            f"Progress: [------------------------------------------------->] 100%\n"
            f"Successfully processed {total_renditions} rendition(s)\n",
        )

        # checking if the number of renditions now equal 0
        renditions_now = Rendition.objects.all()
        total_renditions_now = len(renditions_now)
        self.assertEqual(total_renditions_now, 0)

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    )
    def test_image_renditions_with_cache(self):
        total_renditions = Rendition.objects.count()
        output = self.run_command()
        output_string = self.REAESC.sub("", output.read())
        self.assertIn(
            f"Successfully processed {total_renditions} rendition(s)\n", output_string
        )

        # Run the command again with a warmed cache
        output = self.run_command()
        output_string = self.REAESC.sub("", output.read())
        self.assertIn(
            f"Successfully processed {total_renditions} rendition(s)\n", output_string
        )


@tag("transaction")
class TestUpdateImageRenditionsFileDeletion(TransactionTestCase):
    """
    Rendition file deletion happens in a post_delete handler that defers the
    storage delete to transaction.on_commit, so these have to run as a
    TransactionTestCase for the callback to fire at all.
    """

    def setUp(self):
        # TransactionTestCase does not load the migration fixtures.
        Collection.objects.get_or_create(name="Root", path="0001", depth=1, numchild=0)
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_image.png", colour="white"),
        )

    def test_regenerated_rendition_file_survives(self):
        rendition = self.image.get_rendition("width-100")
        storage = rendition.file.storage
        filename = rendition.file.name
        self.assertTrue(storage.exists(filename))

        management.call_command("wagtail_update_image_renditions", stdout=StringIO())

        rendition = self.image.renditions.get(filter_spec="width-100")
        self.assertTrue(
            rendition.file.storage.exists(rendition.file.name),
            f"{rendition.file.name} was deleted after being regenerated",
        )

    def test_regenerated_rendition_file_survives_when_the_old_file_is_missing(self):
        # The reported case: the rendition rows are in the database but
        # /media/images has been emptied, so the regenerated file lands on
        # exactly the name the deleted rendition had.
        rendition = self.image.get_rendition("width-100")
        storage = rendition.file.storage
        filename = rendition.file.name
        storage.delete(filename)
        self.assertFalse(storage.exists(filename))

        management.call_command("wagtail_update_image_renditions", stdout=StringIO())

        rendition = self.image.renditions.get(filter_spec="width-100")
        self.assertTrue(
            rendition.file.storage.exists(rendition.file.name),
            f"{rendition.file.name} was deleted after being regenerated",
        )
