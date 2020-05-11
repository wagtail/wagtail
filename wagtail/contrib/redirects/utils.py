from wagtail.contrib.redirects.base_formats import DEFAULT_FORMATS
from wagtail.contrib.redirects.tmp_storages import TempFolderStorage


def write_to_tmp_storage(import_file, input_format):
    tmp_storage = TempFolderStorage()
    data = bytes()
    for chunk in import_file.chunks():
        data += chunk

    tmp_storage.save(data, input_format.get_read_mode())
    return tmp_storage


def get_import_formats():
    return [f for f in DEFAULT_FORMATS if f().can_import()]
