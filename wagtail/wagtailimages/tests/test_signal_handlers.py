from __future__ import absolute_import, unicode_literals

from django.db import transaction
from django.test import TestCase, TransactionTestCase

from wagtail.wagtailimages import get_image_model
from wagtail.wagtailimages.tests.utils import get_test_image_file


class TestFilesNotDeletedForDefaultModels(TestCase):
    '''
    Django's TestCase class wraps each test in a transaction and rolls back that
    transaction after each test, in order to provide test isolation. This means
    that no transaction is ever actually committed, thus your on_commit()
    callbacks will never be run. If you need to test the results of an
    on_commit() callback, use a TransactionTestCase instead.
    https://docs.djangoproject.com/en/1.10/topics/db/transactions/#use-in-tests
    
    Because of this, checking that the files are not deleted in this test means
    that the delete signal handler is waiting for on_commit
    '''
    
    def setUp(self):
        self.image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        self.rendition = self.image.get_rendition('original')

    def test_image_file_not_deleted(self):
        file_name = self.image.file.name
        self.assertTrue(self.image.file.storage.exists(file_name))
        self.image.delete()
        self.assertTrue(self.image.file.storage.exists(file_name))
    
    def test_rendition_file_not_deleted(self):
        file_name = self.rendition.file.name
        self.assertTrue(self.rendition.file.storage.exists(file_name))
        self.rendition.delete()
        self.assertTrue(self.rendition.file.storage.exists(file_name))


class TestFilesDeletedForDefaultModels(TransactionTestCase):
    '''
    Django's TestCase class wraps each test in a transaction and rolls back that
    transaction after each test, in order to provide test isolation. This means
    that no transaction is ever actually committed, thus your on_commit()
    callbacks will never be run. If you need to test the results of an
    on_commit() callback, use a TransactionTestCase instead.
    https://docs.djangoproject.com/en/1.10/topics/db/transactions/#use-in-tests
    
    Because we expect file deletion to only happen once a transaction is
    successfully committed, we must run these tests using TransactionTestCase
    '''
    
    # indicate that these tests need the initial data loaded in migrations which
    # is not available by default for TransactionTestCase per
    # https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
    serialized_rollback = True
    
    def test_image_file_deleted(self):
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        self.assertTrue(image.file.storage.exists(image.file.name))
        with transaction.atomic():
            image.delete()
        self.assertFalse(image.file.storage.exists(image.file.name))
    
    def test_rendition_file_deleted(self):
        image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
        rendition = image.get_rendition('original')
        self.assertTrue(rendition.file.storage.exists(rendition.file.name))
        rendition.delete()
        self.assertFalse(rendition.file.storage.exists(rendition.file.name))
