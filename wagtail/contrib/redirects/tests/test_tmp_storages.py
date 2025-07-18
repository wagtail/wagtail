from django.core.cache import cache
from django.test import TestCase

from wagtail.contrib.redirects.tmp_storages import CacheStorage


class CacheStorageTests(TestCase):
    def test_cache_storage_save_and_remove(self):
        name = "testfile.txt"
        content = b"hello world"
        storage = CacheStorage(name)

        # Adds to cache
        storage.save(content)
        key = storage.CACHE_PREFIX + storage.name
        self.assertEqual(cache.get(key), content)

        # Removes from cache
        storage.remove()
        self.assertIsNone(cache.get(key))
