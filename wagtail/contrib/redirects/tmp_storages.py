"""
Copyright (c) Bojan Mihelac and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# Copied from: https://raw.githubusercontent.com/django-import-export/django-import-export/ad004e993a5b766596e7954d130253321c77d81c/import_export/tmp_storages.py
import os
import tempfile
from uuid import uuid4

from django.core.cache import cache
from django.core.files.base import ContentFile


class BaseStorage:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None)
        self.read_mode = kwargs.get("read_mode", "r")
        self.encoding = kwargs.get("encoding", None)

    def save(self, data):
        raise NotImplementedError

    def read(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError


class TempFolderStorage(BaseStorage):
    def save(self, data):
        with self._open(mode="w") as file:
            file.write(data)

    def read(self, read_mode="r"):
        with self._open(mode=read_mode) as file:
            return file.read()

    def remove(self):
        os.remove(self.get_full_path())

    def get_full_path(self):
        return os.path.join(tempfile.gettempdir(), self.name)

    def _open(self, mode="r"):
        if self.name:
            return open(self.get_full_path(), mode, encoding=self.encoding)
        else:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            self.name = tmp_file.name
            return tmp_file


class CacheStorage(BaseStorage):
    """
    By default memcache maximum size per key is 1MB, be careful with large files.
    """

    CACHE_LIFETIME = 86400
    CACHE_PREFIX = "django-import-export-"

    def save(self, data):
        if not self.name:
            self.name = uuid4().hex
        cache.set(self.CACHE_PREFIX + self.name, data, self.CACHE_LIFETIME)

    def read(self, read_mode="r"):
        return cache.get(self.CACHE_PREFIX + self.name)

    def remove(self):
        cache.delete(self.CACHE_PREFIX + self.name)

class MediaStorage(BaseStorage):
    _storage = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._configure_storage()
        self.MEDIA_FOLDER = kwargs.get("MEDIA_FOLDER", "django-import-export")
        kwargs.update({"read_mode": "rb"})
        super().__init__(**kwargs)

    def _configure_storage(self):
        from django.core.files.storage import StorageHandler

        sh = StorageHandler()
        self._storage = (
            sh["import_export"] if "import_export" in sh.backends else sh["default"]
        )

    def save(self, data):
        if not self.name:
            self.name = uuid4().hex
        self._storage.save(self.get_full_path(), ContentFile(data))

    def read(self):
        with self._storage.open(self.get_full_path(), mode=self.read_mode) as f:
            return f.read()

    def remove(self):
        self._storage.delete(self.get_full_path())

    def get_full_path(self):
        if self.MEDIA_FOLDER is not None:
            return os.path.join(self.MEDIA_FOLDER, self.name)
        return self.name