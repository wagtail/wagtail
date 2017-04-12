from __future__ import absolute_import, unicode_literals

import unittest

from django.db import transaction
from django.test import TestCase, TransactionTestCase, override_settings

from wagtail.wagtailcore.models import Collection
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
    
    def setUp(self):
        # Required to create root collection because the TransactionTestCase
        # does not make initial data loaded in migrations available and
        # serialized_rollback=True causes other problems in the test suite.
        # ref: https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
        Collection.objects.get_or_create(
            name="Root",
            path='0001',
            depth=1,
            numchild=0,
        )
    
    def test_oncommit_available(self):
        self.assertEqual(hasattr(transaction, 'on_commit'), signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE)
    
    @unittest.skipUnless(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'is required for this test')
    def test_image_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            self.assertTrue(image.file.storage.exists(image.file.name))
            image.delete()
            self.assertTrue(image.file.storage.exists(image.file.name))
        self.assertFalse(image.file.storage.exists(image.file.name))
    
    @unittest.skipIf(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'duplicate')
    def test_image_file_deleted(self):
        '''
            this test duplicates `test_image_file_deleted_oncommit` for
            django 1.8 support and can be removed once django 1.8 is no longer
            supported
        '''
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            self.assertTrue(image.file.storage.exists(image.file.name))
            image.delete()
        self.assertFalse(image.file.storage.exists(image.file.name))
    
    @unittest.skipUnless(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'is required for this test')
    def test_rendition_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            rendition = image.get_rendition('original')
            self.assertTrue(rendition.file.storage.exists(rendition.file.name))
            rendition.delete()
            self.assertTrue(rendition.file.storage.exists(rendition.file.name))
        self.assertFalse(rendition.file.storage.exists(rendition.file.name))
    
    @unittest.skipIf(signal_handlers.TRANSACTION_ON_COMMIT_AVAILABLE, 'duplicate')
    def test_rendition_file_deleted(self):
        '''
            this test duplicates `test_rendition_file_deleted_oncommit` for
            django 1.8 support and can be removed once django 1.8 is no longer
            supported
        '''
        with transaction.atomic():
            image = get_image_model().objects.create(title="Test Image", file=get_test_image_file())
            rendition = image.get_rendition('original')
            self.assertTrue(rendition.file.storage.exists(rendition.file.name))
            rendition.delete()
        self.assertFalse(rendition.file.storage.exists(rendition.file.name))


@override_settings(WAGTAILIMAGES_IMAGE_MODEL='tests.CustomImage')
class TestFilesDeletedForCustomModels(TestFilesDeletedForDefaultModels):
    def setUp(self):
        # Required to create root collection because the TransactionTestCase
        # does not make initial data loaded in migrations available and
        # serialized_rollback=True causes other problems in the test suite.
        # ref: https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
        Collection.objects.get_or_create(
            name="Root",
            path='0001',
            depth=1,
            numchild=0,
        )
        
        #: Sadly signal receivers only get connected when starting django.
        #: We will re-attach them here to mimic the django startup behavior
        #: and get the signals connected to our custom model..
        signal_handlers.register_signal_handlers()

    def test_image_model(self):
        cls = get_image_model()
        self.assertEqual('%s.%s' % (cls._meta.app_label, cls.__name__), 'tests.CustomImage')
    