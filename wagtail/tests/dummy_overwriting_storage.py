# This file contains a file storage backend that overwrites old files using the same
# name. This is e g the default setting for django_storages.S3Boto3Storage

# The following behaviours have been changed in this backend:
#  - .get_available_name returns the name unchanged
#  - ._save is simplified to doing nothing but saving the file
import os.path

from django.core.files.storage import FileSystemStorage


class DummyOverWritingFileStorage(FileSystemStorage):
    """Mock storage class that does not change file names."""

    def get_available_name(self, name, max_length=None):
        return name

    def _save(self, name, content):
        full_path = self.path(name)
        open(full_path, "wb").write(content.read())
        return os.path.relpath(full_path, self.location)
