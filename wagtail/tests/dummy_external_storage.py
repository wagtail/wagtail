# This file contains a file storage backend that imitates behaviours of
# common external storage backends (S3 boto, libcloud, etc).

# The following behaviours have been added to this backend:
#  - Calling .path on the storage or image file raises NotImplementedError
#  - File.open() after the file has been closed raises an error
#  - File.size exceptions raise DummyExternalStorageError

from django.core.files.base import File
from django.core.files.storage import FileSystemStorage, Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DummyExternalStorage(Storage):
    def __init__(self, *args, **kwargs):
        self.wrapped = FileSystemStorage(*args, **kwargs)

    def path(self, name):
        # Overridden to give it the behaviour of the base Storage class
        # This is what an external storage backend would have
        raise NotImplementedError("This backend doesn't support absolute paths.")

    def _open(self, name, mode='rb'):
        # Overridden to return a DummyExternalStorageFile instead of a normal
        # File object
        return DummyExternalStorageFile(open(self.wrapped.path(name), mode))

    # Wrap all other functions

    def _save(self, name, content):
        return self.wrapped._save(name, content)

    def delete(self, name):
        self.wrapped.delete(name)

    def exists(self, name):
        return self.wrapped.exists(name)

    def listdir(self, path):
        return self.wrapped.listdir(path)

    def size(self, name):
        return self.wrapped.size(name)

    def url(self, name):
        return self.wrapped.url(name)

    def accessed_time(self, name):
        return self.wrapped.accessed_time(name)

    def created_time(self, name):
        return self.wrapped.created_time(name)

    def modified_time(self, name):
        return self.wrapped.modified_time(name)


class DummyExternalStorageError(Exception):
    pass


class DummyExternalStorageFile(File):
    def open(self, mode=None):
        # Based on:
        # https://github.com/django/django/blob/2c39f282b8389f47fee4b24e785a58567c6c3629/django/core/files/base.py#L135-L141

        # I've commented out two lines of this function which stops it checking
        # the filesystem for the file. Making it behave as if it is using an
        # external file storage.

        if not self.closed:
            self.seek(0)
        # elif self.name and os.path.exists(self.name):
        #    self.file = open(self.name, mode or self.mode)
        else:
            raise ValueError("The file cannot be reopened.")

    def size(self):
        try:
            return super().size
        except Exception as e:
            raise DummyExternalStorageError(str(e))
