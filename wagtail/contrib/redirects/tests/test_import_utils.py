import hashlib
import os

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from wagtail.contrib.redirects.utils import (
    get_file_storage,
    get_import_formats,
    write_to_file_storage,
)

TEST_ROOT = os.path.abspath(os.path.dirname(__file__))


class TestImportUtils(TestCase):
    def test_writing_file_with_format(self):
        f = "{}/files/example.csv".format(TEST_ROOT)
        (_, filename) = os.path.split(f)

        with open(f, "rb") as infile:
            content_orig = infile.read()
            upload_file = ContentFile(content_orig)

            import_formats = get_import_formats()
            import_formats = [x for x in import_formats if x.__name__ == "CSV"]
            input_format = import_formats[0]()
            file_storage = write_to_file_storage(upload_file, input_format)

            self.assertEqual(type(file_storage).__name__, "TempFolderStorage")

            file_orig_checksum = hashlib.md5()
            file_orig_checksum.update(content_orig)
            file_orig_checksum = file_orig_checksum.hexdigest()

            file_new_checksum = hashlib.md5()
            with open(file_storage.get_full_path(), "rb") as file_new:
                file_new_checksum.update(file_new.read())
            file_new_checksum = file_new_checksum.hexdigest()

            self.assertEqual(file_orig_checksum, file_new_checksum)

    @override_settings(WAGTAIL_REDIRECTS_FILE_STORAGE="cache")
    def test_that_cache_storage_are_returned(self):
        FileStorage = get_file_storage()
        self.assertEqual(FileStorage.__name__, "RedirectsCacheStorage")

    def test_that_temp_folder_storage_are_returned_as_default(self):
        FileStorage = get_file_storage()
        self.assertEqual(FileStorage.__name__, "TempFolderStorage")

    @override_settings(WAGTAIL_REDIRECTS_FILE_STORAGE="INVALID")
    def test_invalid_file_storage_raises_errors(self):
        with self.assertRaisesMessage(
            Exception, "Invalid file storage, must be either 'tmp_file' or 'cache'"
        ):
            get_file_storage()
