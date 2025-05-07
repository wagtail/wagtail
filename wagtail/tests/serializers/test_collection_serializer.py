import pytest

from wagtail.models import Collection
from wagtail.serializers.collection_serializer import CollectionSerializer


@pytest.mark.django_db
def test_collection():
    root = Collection.get_first_root_node()
    collection = root.add_child(name="test")
    serializer = CollectionSerializer(collection)
    assert serializer.data["name"] == "test"
