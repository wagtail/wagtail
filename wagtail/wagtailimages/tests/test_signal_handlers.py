from __future__ import absolute_import, unicode_literals

from django.db import transaction
from django.test import TestCase, TransactionTestCase

from wagtail.wagtailimages import get_image_model, signal_handlers
from wagtail.wagtailimages.tests.utils import get_test_image_file


class TestFilesDeletedForDefaultModels(TransactionTestCase):
    '''
    Because we expect file deletion to only happen once a transaction is
    successfully committed, we must run these tests using TransactionTestCase
    per the following documentation:
    
        Django's TestCase class wraps each test in a transaction and rolls back that
        transaction after each test, in order to provide test isolation. This means
        that no transaction is ever actually committed, thus your on_commit()
        callbacks will never be run. If you need to test the results of an
        on_commit() callback, use a TransactionTestCase instead.
        https://docs.djangoproject.com/en/1.10/topics/db/transactions/#use-in-tests
    '''
    
    # indicate that these tests need the initial data loaded in migrations which
    # is not available by default for TransactionTestCase per
    # https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
    serialized_rollback = True
    
    def test_oncommit_available(self):
        self.assertEqual(hasattr(transaction, 'on_commit'), signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE)
    
    def test_image_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            self.assertTrue(image.file.storage.exists(image.file.name))
            image.delete()
            if signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE:
                self.assertTrue(image.file.storage.exists(image.file.name))
        self.assertFalse(image.file.storage.exists(image.file.name))
    
    def test_rendition_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            rendition = image.get_rendition('original')
            self.assertTrue(rendition.file.storage.exists(rendition.file.name))
            rendition.delete()
            if signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE:
                self.assertTrue(rendition.file.storage.exists(rendition.file.name))
        self.assertFalse(rendition.file.storage.exists(rendition.file.name))
