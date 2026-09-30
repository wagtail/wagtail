from unittest import mock

from django.db import transaction
from django.test import TestCase, TransactionTestCase, override_settings, tag

from wagtail.images import get_image_model, signal_handlers
from wagtail.images.rect import Rect
from wagtail.images.tasks import set_image_focal_point_task
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Collection
from wagtail.test.utils import PageFixturesMixin

from .utils import Image


@tag("transaction")
class TestFilesDeletedForDefaultModels(TransactionTestCase):
    """
    Because we expect file deletion to only happen once a transaction is
    successfully committed, we must run these tests using TransactionTestCase
    per the following documentation:

        Django's TestCase class wraps each test in a transaction and rolls back that
        transaction after each test, in order to provide test isolation. This means
        that no transaction is ever actually committed, thus your on_commit()
        callbacks will never be run. If you need to test the results of an
        on_commit() callback, use a TransactionTestCase instead.
        https://docs.djangoproject.com/en/1.10/topics/db/transactions/#use-in-tests
    """

    def setUp(self):
        # Required to create root collection because the TransactionTestCase
        # does not make initial data loaded in migrations available and
        # serialized_rollback=True causes other problems in the test suite.
        # ref: https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
        Collection.objects.get_or_create(
            name="Root",
            path="0001",
            depth=1,
            numchild=0,
        )

    def test_image_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(
                title="Test Image",
                description="A test description",
                file=get_test_image_file(),
            )
            filename = image.file.name
            self.assertTrue(image.file.storage.exists(filename))
            image.delete()
            self.assertTrue(image.file.storage.exists(filename))
        self.assertFalse(image.file.storage.exists(filename))

    def test_rendition_file_deleted_oncommit(self):
        with transaction.atomic():
            image = get_image_model().objects.create(
                title="Test Image",
                description="A test description",
                file=get_test_image_file(),
            )
            rendition = image.get_rendition("original")
            filename = rendition.file.name
            self.assertTrue(rendition.file.storage.exists(filename))
            rendition.delete()
            self.assertTrue(rendition.file.storage.exists(filename))
        self.assertFalse(rendition.file.storage.exists(filename))


@override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
class TestFilesDeletedForCustomModels(TestFilesDeletedForDefaultModels):
    def setUp(self):
        # Required to create root collection because the TransactionTestCase
        # does not make initial data loaded in migrations available and
        # serialized_rollback=True causes other problems in the test suite.
        # ref: https://docs.djangoproject.com/en/1.10/topics/testing/overview/#rollback-emulation
        Collection.objects.get_or_create(
            name="Root",
            path="0001",
            depth=1,
            numchild=0,
        )

        #: Sadly signal receivers only get connected when starting django.
        #: We will re-attach them here to mimic the django startup behaviour
        #: and get the signals connected to our custom model..
        signal_handlers.register_signal_handlers()

    def test_image_model(self):
        cls = get_image_model()
        self.assertEqual(f"{cls._meta.app_label}.{cls.__name__}", "tests.CustomImage")


@override_settings(WAGTAILIMAGES_FEATURE_DETECTION_ENABLED=True)
class TestRawForPreSaveImageFeatureDetection(PageFixturesMixin, TestCase):
    fixtures = ["test.json"]

    # just to test the file is from a fixture doesn't actually exists.
    # raw check in pre_save_image_feature_detection skips on the provided condition of this test
    # hence avoiding an error

    def test_image_does_not_exist(self):
        bad_image = Image.objects.get(pk=1)
        self.assertFalse(bad_image.file.storage.exists(bad_image.file.name))


@override_settings(WAGTAILIMAGES_FEATURE_DETECTION_ENABLED=True)
class TestQueuedFocalPointDetection(TestCase):
    def test_editor_crop_survives_queued_detection(self):
        with mock.patch(
            "wagtail.images.signal_handlers.set_image_focal_point_task"
        ) as queued_task:
            automatic = Image.objects.create(
                title="Automatic", file=get_test_image_file()
            )
            edited = Image.objects.create(title="Edited", file=get_test_image_file())
        self.assertEqual(queued_task.enqueue.call_count, 2)

        manual_crop = Rect(40, 40, 80, 80)
        edited.set_focal_point(manual_crop)
        edited.save(
            update_fields=(
                "focal_point_x",
                "focal_point_y",
                "focal_point_width",
                "focal_point_height",
            )
        )

        detected_crop = Rect(10, 10, 30, 30)
        with mock.patch.object(
            Image, "get_suggested_focal_point", return_value=detected_crop
        ):
            set_image_focal_point_task.call(
                automatic._meta.app_label, automatic._meta.model_name, automatic.pk
            )
            set_image_focal_point_task.call(
                edited._meta.app_label, edited._meta.model_name, edited.pk
            )

        automatic.refresh_from_db()
        edited.refresh_from_db()
        self.assertEqual(automatic.get_focal_point(), detected_crop)
        self.assertEqual(edited.get_focal_point(), manual_crop)

    def test_editor_crop_set_during_detection_survives(self):
        with mock.patch("wagtail.images.signal_handlers.set_image_focal_point_task"):
            image = Image.objects.create(title="Edited", file=get_test_image_file())

        manual_crop = Rect(40, 40, 80, 80)
        detected_crop = Rect(10, 10, 30, 30)

        def detect_after_edit(_image):
            edited = Image.objects.get(pk=image.pk)
            edited.set_focal_point(manual_crop)
            edited.save(
                update_fields=(
                    "focal_point_x",
                    "focal_point_y",
                    "focal_point_width",
                    "focal_point_height",
                )
            )
            return detected_crop

        with mock.patch.object(
            Image, "get_suggested_focal_point", new=detect_after_edit
        ):
            set_image_focal_point_task.call(
                image._meta.app_label, image._meta.model_name, image.pk
            )

        image.refresh_from_db()
        self.assertEqual(image.get_focal_point(), manual_crop)
