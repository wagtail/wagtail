import hashlib
import os

from django.core.files.base import ContentFile
from django.test import TestCase

from wagtail.contrib.redirects.utils import get_import_formats, write_to_tmp_storage


TEST_ROOT = os.path.abspath(os.path.dirname(__file__))


class TestImportUtils(TestCase):
    def test_writing_file_with_format(self):
        f = "{}/files/example.csv".format(TEST_ROOT)
        (_, filename) = os.path.split(f)

        with open(f, "rb") as infile:

            content_orig = infile.read()
            upload_file = ContentFile(content_orig)

            import_formats = get_import_formats()
            import_formats = [
                x for x in import_formats if x.__name__ == "CSV"
            ]
            input_format = import_formats[0]()
            storage = write_to_tmp_storage(upload_file, input_format)

            self.assertEqual(type(storage).__name__, "TempFolderStorage")

            file_orig_checksum = hashlib.md5()
            file_orig_checksum.update(content_orig)
            file_orig_checksum = file_orig_checksum.hexdigest()

            file_new_checksum = hashlib.md5()
            with open(storage.get_full_path(), "rb") as file_new:
                file_new_checksum.update(file_new.read())
            file_new_checksum = file_new_checksum.hexdigest()

            self.assertEqual(file_orig_checksum, file_new_checksum)
