import pytest
from django.core.cache import cache
from wagtail.contrib.redirects.tmp_storages import CacheStorage

@pytest.mark.django_db
def test_cache_storage_save_and_remove():
    name = "testfile.txt"
    content = b"hello world"
    storage = CacheStorage(name)
    
    # Ajoute au cache
    storage.save(content)
    key = storage.CACHE_PREFIX + storage.name
    assert cache.get(key) == content
    
    # Supprime du cache
    storage.remove()
    assert cache.get(key) is None
