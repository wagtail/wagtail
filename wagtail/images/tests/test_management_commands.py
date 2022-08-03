import re
import warnings
from io import StringIO

from django.core import management
from django.test import TestCase

from wagtail.images import get_image_model

from .utils import Image, get_test_image_file


class TestUpdateImageRenditions(TestCase):
    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(filename="test_image.png", colour="white"),
        )

        self.rendition = Image.get_rendition_model().objects.create(
            image=self.image,
            filter_spec="original",
            width=1000,
            height=1000,
            file=get_test_image_file(
                filename="test_rendition.png", colour="white", size=(1000, 1000)
            ),
        )

    def delete_renditions(self):
        renditions = get_image_model().get_rendition_model().objects.all()
        for rendition in renditions:
            try:
                rendition_image = rendition.image
                rendition.delete()
            except Exception:
                warnings.warn(f"Could not delete rendition for {rendition_image}")

    def run_command(self, **options):
        output = StringIO()
        management.call_command(
            "wagtail_update_image_renditions", stdout=output, **options
        )
        output.seek(0)

        return output

    def test_exits_early_for_no_renditions(self):
        self.delete_renditions()
        # checking when command is called without any arguments
        output = self.run_command()
        self.assertEqual(output.read(), "No image renditions found.\n")

        # checking when command is called with '--purge-only'
        output = self.run_command(purge_only=True)
        self.assertEqual(output.read(), "No image renditions found.\n")

    def test_image_renditions(self):
        renditions = get_image_model().get_rendition_model().objects.all()
        total_renditions = len(renditions)
        output = self.run_command()
        reaesc = re.compile(r"\x1b[^m]*m")
        output_string = reaesc.sub("", output.read())
        # checking if the number of renditions regenerated equal total_renditions
        self.assertEqual(
            output_string,
            f"Successfully regenerated {total_renditions} image rendition(s)\n",
        )

        # checking if the number of renditions now equal total_renditions
        renditions_now = get_image_model().get_rendition_model().objects.all()
        total_renditions_now = len(renditions_now)
        self.assertEqual(total_renditions_now, total_renditions)

    def test_image_renditions_with_purge_only(self):
        renditions = get_image_model().get_rendition_model().objects.all()
        total_renditions = len(renditions)
        output = self.run_command(purge_only=True)
        reaesc = re.compile(r"\x1b[^m]*m")
        output_string = reaesc.sub("", output.read())
        # checking if the number of renditions purged equal total_renditions
        self.assertEqual(
            output_string,
            f"Successfully purged {total_renditions} image rendition(s)\n",
        )

        # checking if the number of renditions now equal 0
        renditions_now = get_image_model().get_rendition_model().objects.all()
        total_renditions_now = len(renditions_now)
        self.assertEqual(total_renditions_now, 0)
