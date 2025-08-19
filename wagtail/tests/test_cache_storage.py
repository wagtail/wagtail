from django.test import TestCase
from import_export.tmp_storages import CacheStorage


class TestCacheStorage(TestCase):
    def test_save_and_read(self):
        storage = CacheStorage()
        storage.save("hello world")
        self.assertEqual(storage.read(), "hello world")

    def test_remove(self):
        storage = CacheStorage()
        storage.save("temp-data")
        storage.remove()
        self.assertIsNone(storage.read())
