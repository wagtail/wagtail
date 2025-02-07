from django.test import TestCase

from wagtail.signal_handlers import update_reference_index_on_save
from wagtail.test.testapp.models import AdvertWithCustomUUIDPrimaryKey


class TestUpdateReferenceIndexOnSave(TestCase):
    def test_update_reference_signal_with_uuid_pk(self):
        instance = AdvertWithCustomUUIDPrimaryKey()
        instance.save()
        update_reference_index_on_save(instance)
