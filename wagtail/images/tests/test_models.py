import unittest

from django.contrib.auth.models import Group, Permission
from django.core.cache import caches
from django.core.files import File
from django.core.files.storage import DefaultStorage, Storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Prefetch
from django.db.utils import IntegrityError
from django.test import SimpleTestCase, TestCase, TransactionTestCase
from django.urls import reverse
from willow.image import Image as WillowImage

from wagtail.images.models import (
    Filter,
    Picture,
    Rendition,
    ResponsiveImage,
    SourceImageIOError,
    get_rendition_storage,
)
from wagtail.images.rect import Rect
from wagtail.models import Collection, GroupCollectionPermission, Page, ReferenceIndex
from wagtail.test.testapp.models import (
    EventPage,
    EventPageCarouselItem,
    ReimportedImageModel,
)
from wagtail.test.utils import WagtailTestUtils, override_settings

from .utils import (
    Image,
    get_test_image_file,
    get_test_image_file_svg,
    get_test_image_filename,
)


class CustomStorage(Storage):
    def __init__(self):
        super().__init__()


class TestImage(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(colour="white"),
        )

    def test_get_image_model_at_import_time(self):
        self.assertEqual(ReimportedImageModel, Image)

    def test_is_portrait(self):
        self.assertFalse(self.image.is_portrait())

    def test_is_landscape(self):
        self.assertTrue(self.image.is_landscape())

    def test_get_rect(self):
        self.assertEqual(self.image.get_rect(), Rect(0, 0, 640, 480))

    def test_get_focal_point(self):
        self.assertIsNone(self.image.get_focal_point())

        # Add a focal point to the image
        self.image.focal_point_x = 100
        self.image.focal_point_y = 200
        self.image.focal_point_width = 50
        self.image.focal_point_height = 20

        # Get it
        self.assertEqual(self.image.get_focal_point(), Rect(75, 190, 125, 210))

    def test_has_focal_point(self):
        self.assertFalse(self.image.has_focal_point())

        # Add a focal point to the image
        self.image.focal_point_x = 100
        self.image.focal_point_y = 200
        self.image.focal_point_width = 50
        self.image.focal_point_height = 20

        self.assertTrue(self.image.has_focal_point())

    def test_set_focal_point(self):
        self.assertIsNone(self.image.focal_point_x)
        self.assertIsNone(self.image.focal_point_y)
        self.assertIsNone(self.image.focal_point_width)
        self.assertIsNone(self.image.focal_point_height)

        self.image.set_focal_point(Rect(100, 150, 200, 350))

        self.assertEqual(self.image.focal_point_x, 150)
        self.assertEqual(self.image.focal_point_y, 250)
        self.assertEqual(self.image.focal_point_width, 100)
        self.assertEqual(self.image.focal_point_height, 200)

        self.image.set_focal_point(None)

        self.assertIsNone(self.image.focal_point_x)
        self.assertIsNone(self.image.focal_point_y)
        self.assertIsNone(self.image.focal_point_width)
        self.assertIsNone(self.image.focal_point_height)

    def test_is_stored_locally(self):
        self.assertTrue(self.image.is_stored_locally())

    @override_settings(
        DEFAULT_FILE_STORAGE="wagtail.test.dummy_external_storage.DummyExternalStorage"
    )
    def test_is_stored_locally_with_external_storage(self):
        self.assertFalse(self.image.is_stored_locally())

    def test_get_file_size(self):
        file_size = self.image.get_file_size()
        self.assertIsInstance(file_size, int)
        self.assertGreater(file_size, 0)

    def test_get_file_size_on_missing_file_raises_sourceimageioerror(self):
        self.image.file.delete(save=False)
        with self.assertRaises(SourceImageIOError):
            self.image.get_file_size()

    def test_file_hash(self):
        self.assertEqual(
            self.image.get_file_hash(), "4dd0211870e130b7e1690d2ec53c499a54a48fef"
        )

    def test_get_suggested_focal_point_svg(self):
        """
        Feature detection should not be run on SVGs.

        https://github.com/wagtail/wagtail/issues/11172
        """
        image = Image.objects.create(
            title="Test SVG",
            file=get_test_image_file_svg(),
        )
        self.assertIsNone(image.get_suggested_focal_point())


class TestImageQuerySet(TransactionTestCase):
    fixtures = ["test_empty.json"]

    def test_search_method(self):
        # Create an image for running tests on
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Search for it
        results = Image.objects.search("Test")
        self.assertEqual(list(results), [image])

    def test_operators(self):
        aaa_image = Image.objects.create(
            title="AAA Test image",
            file=get_test_image_file(),
        )
        zzz_image = Image.objects.create(
            title="ZZZ Test image",
            file=get_test_image_file(),
        )

        results = Image.objects.search("aaa test", operator="and")
        self.assertEqual(list(results), [aaa_image])

        results = Image.objects.search("aaa test", operator="or")
        sorted_results = sorted(results, key=lambda img: img.title)
        self.assertEqual(sorted_results, [aaa_image, zzz_image])

    def test_custom_ordering(self):
        aaa_image = Image.objects.create(
            title="AAA Test image",
            file=get_test_image_file(),
        )
        zzz_image = Image.objects.create(
            title="ZZZ Test image",
            file=get_test_image_file(),
        )

        results = Image.objects.order_by("title").search(
            "Test", order_by_relevance=False
        )
        self.assertEqual(list(results), [aaa_image, zzz_image])
        results = Image.objects.order_by("-title").search(
            "Test", order_by_relevance=False
        )
        self.assertEqual(list(results), [zzz_image, aaa_image])

    def test_search_indexing_prefetches_tags(self):
        for i in range(0, 10):
            image = Image.objects.create(
                title="Test image %d" % i,
                file=get_test_image_file(),
            )
            image.tags.add("aardvark", "artichoke", "armadillo")

        with self.assertNumQueries(2):
            results = {
                image.title: [tag.name for tag in image.tags.all()]
                for image in Image.get_indexed_objects()
            }
            self.assertIn("aardvark", results["Test image 0"])


class TestImagePermissions(WagtailTestUtils, TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
        self.user = self.create_user(
            username="user", email="user@email.com", password="password"
        )
        self.owner = self.create_user(
            username="owner", email="owner@email.com", password="password"
        )
        self.editor = self.create_user(
            username="editor", email="editor@email.com", password="password"
        )
        self.editor.groups.add(Group.objects.get(name="Editors"))
        self.administrator = self.create_superuser(
            username="administrator",
            email="administrator@email.com",
            password="password",
        )

        # Owner user must have the add_image permission
        image_adders_group = Group.objects.create(name="Image adders")
        GroupCollectionPermission.objects.create(
            group=image_adders_group,
            collection=Collection.get_first_root_node(),
            permission=Permission.objects.get(codename="add_image"),
        )
        self.owner.groups.add(image_adders_group)

        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            uploaded_by_user=self.owner,
            file=get_test_image_file(),
        )

    def test_administrator_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.administrator))

    def test_editor_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.editor))

    def test_owner_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.owner))

    def test_user_cant_edit(self):
        self.assertFalse(self.image.is_editable_by_user(self.user))


class TestFilters(SimpleTestCase):
    def test_expand_spec_single(self):
        self.assertEqual(Filter.expand_spec("width-100"), ["width-100"])

    def test_expand_spec_flat(self):
        self.assertEqual(
            Filter.expand_spec("width-100 jpegquality-20"), ["width-100|jpegquality-20"]
        )

    def test_expand_spec_pipe(self):
        self.assertEqual(
            Filter.expand_spec("width-100|jpegquality-20"), ["width-100|jpegquality-20"]
        )

    def test_expand_spec_list(self):
        self.assertEqual(
            Filter.expand_spec(["width-100", "jpegquality-20"]),
            ["width-100|jpegquality-20"],
        )

    def test_expand_spec_braced(self):
        self.assertEqual(
            Filter.expand_spec("width-{100,200}"), ["width-100", "width-200"]
        )

    def test_expand_spec_mixed(self):
        self.assertEqual(
            Filter.expand_spec("width-{100,200} jpegquality-40"),
            ["width-100|jpegquality-40", "width-200|jpegquality-40"],
        )

    def test_expand_spec_mixed_pipe(self):
        self.assertEqual(
            Filter.expand_spec("width-{100,200}|jpegquality-40"),
            ["width-100|jpegquality-40", "width-200|jpegquality-40"],
        )

    def test_expand_spec_multiple_braces(self):
        self.assertEqual(
            Filter.expand_spec("width-{100,200} jpegquality-{40,80} grayscale"),
            [
                "width-100|jpegquality-40|grayscale",
                "width-100|jpegquality-80|grayscale",
                "width-200|jpegquality-40|grayscale",
                "width-200|jpegquality-80|grayscale",
            ],
        )


class TestResponsiveImage(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.rendition_10 = self.image.get_rendition("width-10")

    def test_construct_empty(self):
        img = ResponsiveImage({})
        self.assertEqual(img.renditions, [])
        self.assertEqual(img.attrs, None)

    def test_construct_with_renditions(self):
        renditions = {"a": self.rendition_10}
        img = ResponsiveImage(renditions)
        self.assertEqual(img.renditions, [self.rendition_10])

    def test_evaluate_value(self):
        self.assertFalse(ResponsiveImage({}))
        self.assertFalse(ResponsiveImage({}, {"sizes": "100vw"}))

        renditions = {"a": self.rendition_10}
        self.assertTrue(ResponsiveImage(renditions))

    def test_compare_value(self):
        renditions = {"a": self.rendition_10}
        value1 = ResponsiveImage(renditions)
        value2 = ResponsiveImage(renditions)
        value3 = ResponsiveImage({"a": self.image.get_rendition("width-15")})
        value4 = ResponsiveImage(renditions, {"sizes": "100vw"})
        self.assertNotEqual(value1, value3)
        self.assertNotEqual(value1, 12345)
        self.assertEqual(value1, value2)
        self.assertNotEqual(value1, value4)

    def test_get_width_srcset(self):
        renditions = {
            "width-10": self.rendition_10,
            "width-90": self.image.get_rendition("width-90"),
        }
        filenames = [
            get_test_image_filename(self.image, "width-10"),
            get_test_image_filename(self.image, "width-90"),
        ]
        self.assertEqual(
            ResponsiveImage.get_width_srcset(list(renditions.values())),
            f"{filenames[0]} 10w, {filenames[1]} 90w",
        )

    def test_get_width_srcset_single_rendition(self):
        renditions = {"width-10": self.rendition_10}
        self.assertEqual(
            ResponsiveImage.get_width_srcset(list(renditions.values())),
            get_test_image_filename(self.image, "width-10"),
        )

    def test_render(self):
        renditions = {
            "width-10": self.rendition_10,
            "width-90": self.image.get_rendition("width-90"),
        }
        img = ResponsiveImage(renditions)
        filenames = [
            get_test_image_filename(self.image, "width-10"),
            get_test_image_filename(self.image, "width-90"),
        ]
        self.assertHTMLEqual(
            img.__html__(),
            f"""
                <img
                    alt="Test image"
                    src="{filenames[0]}"
                    srcset="{filenames[0]} 10w, {filenames[1]} 90w"
                    width="10"
                    height="7"
                >
            """,
        )

    def test_render_single_image_same_as_img_tag(self):
        img = ResponsiveImage({"width-10": self.rendition_10})
        self.assertHTMLEqual(img.__html__(), self.rendition_10.img_tag())


class TestPicture(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.rendition_10 = self.image.get_rendition("width-10")

    def test_formats(self):
        renditions = {
            "format-jpeg": self.rendition_10,
            "format-webp": self.rendition_10,
        }
        img = Picture(renditions)
        self.assertEqual(
            img.formats, {"jpeg": [self.rendition_10], "webp": [self.rendition_10]}
        )

    def test_single_format(self):
        renditions = {"format-jpeg": self.rendition_10}
        img = Picture(renditions)
        self.assertEqual(img.formats, {})

    def test_mixed_format(self):
        renditions = {
            "format-jpeg": self.rendition_10,
            "format-webp": self.rendition_10,
            "format-webp-lossless": self.rendition_10,
        }
        img = Picture(renditions)
        self.assertEqual(
            img.formats,
            {
                "jpeg": [self.rendition_10],
                "webp": [self.rendition_10, self.rendition_10],
            },
        )

    def test_fallback_format(self):
        avif = {"format-avif": self.rendition_10}
        webp = {"format-webp": self.rendition_10}
        jpeg = {"format-jpeg": self.rendition_10}
        png = {"format-png": self.rendition_10}
        gif = {"format-gif": self.rendition_10}
        fallbacks = {
            "gif": {**avif, **webp, **jpeg, **png, **gif},
            "png": {**avif, **webp, **jpeg, **png},
            "jpeg": {**avif, **webp, **jpeg},
            "webp": {**avif, **webp},
        }
        for fmt, renditions in fallbacks.items():
            self.assertEqual(Picture(renditions).get_fallback_format(), fmt)

    def test_render_multi_format_sizes(self):
        renditions = {
            "format-jpeg|width-10": self.image.get_rendition("format-jpeg|width-10"),
            "format-jpeg|width-90": self.image.get_rendition("format-jpeg|width-90"),
            "format-webp|width-10": self.image.get_rendition("format-webp|width-10"),
            "format-webp|width-90": self.image.get_rendition("format-webp|width-90"),
        }
        img = Picture(renditions, {"sizes": "100vw"})
        filenames = [
            get_test_image_filename(self.image, "format-jpeg.width-10"),
            get_test_image_filename(self.image, "format-jpeg.width-90"),
            get_test_image_filename(self.image, "format-webp.width-10"),
            get_test_image_filename(self.image, "format-webp.width-90"),
        ]
        self.assertHTMLEqual(
            img.__html__(),
            f"""
                <picture>
                    <source srcset="{filenames[2]} 10w, {filenames[3]} 90w" sizes="100vw" type="image/webp">
                    <img
                        alt="Test image"
                        sizes="100vw"
                        src="{filenames[0]}"
                        srcset="{filenames[0]} 10w, {filenames[1]} 90w"
                        width="10"
                        height="7"
                    >
                </picture>
            """,
        )

    def test_render_single_image_same_as_img_tag(self):
        img = Picture({"width-10": self.rendition_10})
        self.assertHTMLEqual(
            img.__html__(), f"<picture>{self.rendition_10.img_tag()}</picture>"
        )


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class TestRenditions(TestCase):
    SPECS = ("height-66", "width-100", "width-400")

    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_get_rendition_model(self):
        self.assertIs(Image.get_rendition_model(), Rendition)

    def test_minification(self):
        rendition = self.image.get_rendition("width-400")

        # Check size
        self.assertEqual(rendition.width, 400)
        self.assertEqual(rendition.height, 300)

        # check that the rendition has been recorded under the correct filter,
        # via the Rendition.filter_spec attribute (in active use as of Wagtail 1.8)
        self.assertEqual(rendition.filter_spec, "width-400")

    def test_resize_to_max(self):
        rendition = self.image.get_rendition("max-100x100")

        # Check size
        self.assertEqual(rendition.width, 100)
        self.assertEqual(rendition.height, 75)

    def test_resize_to_min(self):
        rendition = self.image.get_rendition("min-120x120")

        # Check size
        self.assertEqual(rendition.width, 160)
        self.assertEqual(rendition.height, 120)

    def test_resize_to_original(self):
        rendition = self.image.get_rendition("original")

        # Check size
        self.assertEqual(rendition.width, 640)
        self.assertEqual(rendition.height, 480)

    def test_cache(self):
        # Get two renditions with the same filter
        first_rendition = self.image.get_rendition("width-400")
        second_rendition = self.image.get_rendition("width-400")

        # Check that they are the same object
        self.assertEqual(first_rendition, second_rendition)

    def test_get_with_filter_instance(self):
        # Get two renditions with the same filter
        first_rendition = self.image.get_rendition("width-400")
        second_rendition = self.image.get_rendition(Filter("width-400"))

        # Check that they are the same object
        self.assertEqual(first_rendition, second_rendition)

    def test_prefetched_rendition_found(self):
        # Request a rendition that does not exist yet
        with self.assertNumQueries(5):
            original_rendition = self.image.get_rendition("width-100")

        # Refetch the same image with all renditions prefetched
        image = Image.objects.prefetch_related("renditions").get(pk=self.image.pk)

        # get_rendition() should return the prefetched rendition
        with self.assertNumQueries(0):
            second_rendition = image.get_rendition("width-100")

        # The renditions should match
        self.assertEqual(original_rendition, second_rendition)

    def test_prefetch_renditions_found(self):
        # Same test as above but uses the `prefetch_renditions` method on the manager instead.
        with self.assertNumQueries(5):
            original_rendition = self.image.get_rendition("width-100")

        image = Image.objects.prefetch_renditions("width-100").get(pk=self.image.pk)

        with self.assertNumQueries(0):
            second_rendition = image.get_rendition("width-100")

        self.assertEqual(original_rendition, second_rendition)

    def test_prefetched_rendition_not_found(self):
        # Request a rendition that does not exist yet
        with self.assertNumQueries(5):
            original_rendition = self.image.get_rendition("width-100")

        # Refetch the same image with all renditions prefetched
        image = Image.objects.prefetch_related("renditions").get(pk=self.image.pk)

        # Request a different rendition from this object
        with self.assertNumQueries(4):
            # The number of queries is fewer than before, because checks for
            # an existing rendition (in cache and db) are skipped
            second_rendition = image.get_rendition("height-66")

        # The renditions should NOT match
        self.assertNotEqual(original_rendition, second_rendition)

        # Request the same rendition again
        with self.assertNumQueries(0):
            # Newly created renditions are appended to the prefetched
            # rendition queryset, so that multiple requests for the same
            # rendition can reuse the same value
            third_rendition = image.get_rendition("height-66")

        # The second and third renditions should be references to the
        # exact same in-memory object
        self.assertIs(second_rendition, third_rendition)

    def test_prefetch_renditions_not_found(self):
        # Same test as above but uses the `prefetch_renditions` method on the manager instead.
        with self.assertNumQueries(5):
            original_rendition = self.image.get_rendition("width-100")

        image = Image.objects.prefetch_renditions("width-100").get(pk=self.image.pk)

        with self.assertNumQueries(4):
            second_rendition = image.get_rendition("height-66")

        self.assertNotEqual(original_rendition, second_rendition)

        with self.assertNumQueries(0):
            third_rendition = image.get_rendition("height-66")

        self.assertIs(second_rendition, third_rendition)

    def test_get_renditions_with_filter_instance(self):
        # Get two renditions with the same filter
        first = list(self.image.get_renditions("width-400").values())
        second = list(self.image.get_renditions(Filter("width-400")).values())

        # Check that they are the same object
        self.assertEqual(first[0], second[0])

    def test_get_renditions_key_order(self):
        # Fetch one of the renditions so it exists before the other two.
        self.image.get_rendition("width-40")
        specs = ["width-30", "width-40", "width-50"]
        renditions_keys = list(self.image.get_renditions(*specs).keys())
        self.assertEqual(renditions_keys, specs)

    def _test_get_renditions_performance(
        self,
        db_queries_expected: int,
        prefetch_restricted: bool = False,
        prefetch_all: bool = False,
    ):
        queryset = Image.objects.all()
        if prefetch_all:
            queryset = queryset.prefetch_related("renditions")
        elif prefetch_restricted:
            queryset = queryset.prefetch_renditions(*self.SPECS)

        image = queryset.get(id=self.image.id)
        with self.assertNumQueries(db_queries_expected):
            image.get_renditions(*self.SPECS)

    def test_get_renditions_performance_with_rendition_caching_disabled(self):
        # ATTEMPT 1
        # 1) An initial lookup for rendition from the DB
        # 2) A check for clashes before bulk saving new renditions
        # 3) A bulk_create() to save new renditions
        self._test_get_renditions_performance(3)

        # ATTEMPT 2
        # With all renditions already created, we should just see
        # 1) An initial lookup for rendition from the DB
        self._test_get_renditions_performance(1)

        # ATTEMPT 3
        # If the existing renditions are prefetched, no futher queries should
        # be needed, whether that's with prefetch_related("renditions") or
        # prefetch_renditions()
        self._test_get_renditions_performance(0, prefetch_all=True)
        self._test_get_renditions_performance(0, prefetch_restricted=True)

    @override_settings(
        CACHES={
            "renditions": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            },
        },
    )
    def test_get_renditions_performance_with_rendition_caching_enabled(self):
        # ATTEMPT 1
        # 1) An initial lookup for rendition from the DB
        # 2) A check for clashes before bulk saving new renditions
        # 3) A bulk_create() to save new renditions
        self._test_get_renditions_performance(3)

        # ATTEMPT 2
        # Any renditions created in the first attempt should have
        # been added to the cache, so a second request should bypass
        # the database completely
        self._test_get_renditions_performance(0)

        # ATTEMPT 3
        # Prefetching renditions should mean that no queries are
        # required, and no cache hits are made
        self._test_get_renditions_performance(0, prefetch_all=True)

    def test_create_renditions(self):
        filter_list = [Filter(spec) for spec in self.SPECS]
        # When no renditions exist, there should be one query for
        # 'clash identification', and another for bulk creation
        with self.assertNumQueries(2):
            result = self.image.create_renditions(*filter_list)

        # Renditions should match the filters
        for filter, rendition in result.items():
            self.assertEqual(filter.spec, rendition.filter_spec)

        # Filter specs should match the filters that were provided as arguments
        self.assertEqual(
            {filter.spec for filter in result.keys()},
            {filter.spec for filter in filter_list},
        )

        # When the renditions already exist, there should be one query
        # for 'clash identification', but that is all
        with self.assertNumQueries(1):
            result = self.image.create_renditions(*filter_list)

        # Renditions should match the filters
        for filter, rendition in result.items():
            self.assertEqual(filter.spec, rendition.filter_spec)

        # Filter specs should match the filters that were provided as arguments
        self.assertEqual(
            {filter.spec for filter in result.keys()},
            {filter.spec for filter in filter_list},
        )

        # Another request should give us an equal result
        with self.assertNumQueries(1):
            second_result = self.image.create_renditions(*filter_list)
        self.assertEqual(result, second_result)

        # When only some renditions exist, we should see the create query
        # once again
        self.image.renditions.filter(filter_spec=self.SPECS[0]).delete()
        with self.assertNumQueries(2):
            third_result = self.image.create_renditions(*filter_list)

        # Equality check should fail, as newly created rendition has a different pk
        self.assertNotEqual(third_result, result)

        # But, we should see equality on the keys
        self.assertEqual(third_result.keys(), result.keys())

    def test_alt_attribute(self):
        rendition = self.image.get_rendition("width-400")
        self.assertEqual(rendition.alt, "Test image")

    def test_full_url(self):
        ren_img = self.image.get_rendition("original")
        full_url = ren_img.full_url
        img_name = ren_img.file.name.split("/")[1]
        self.assertEqual(full_url, f"http://testserver/media/images/{img_name}")

    @override_settings(
        CACHES={
            "renditions": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            },
        },
    )
    def test_renditions_cache(self):
        cache = Rendition.cache_backend
        rendition = self.image.get_rendition("width-500")
        rendition_cache_key = rendition.get_cache_key()

        # Check rendition is saved to cache
        self.assertEqual(cache.get(rendition_cache_key), rendition)

        # Mark a rendition to check it comes from cache
        rendition._mark = "original"
        cache.set(rendition_cache_key, rendition)

        # Check if get_rendition returns the rendition from cache
        with self.assertNumQueries(0):
            new_rendition = self.image.get_rendition("width-500")
        self.assertEqual(new_rendition._mark, "original")

        # But, not if the rendition has been prefetched
        fresh_image = Image.objects.prefetch_related("renditions").get(pk=self.image.pk)
        with self.assertNumQueries(0):
            prefetched_rendition = fresh_image.get_rendition("width-500")
        self.assertFalse(hasattr(prefetched_rendition, "_mark"))

        # changing the image file should invalidate the cache
        self.image.file = get_test_image_file(colour="green")
        self.image.save()
        # deleting renditions would normally happen within the 'edit' view on file change -
        # we're bypassing that here, so have to do it manually
        self.image.renditions.all().delete()
        new_rendition = self.image.get_rendition("width-500")
        self.assertFalse(hasattr(new_rendition, "_mark"))

        # changing it back should also generate a new rendition and not re-use
        # the original one (because that file has now been deleted in the change)
        self.image.file = get_test_image_file(colour="white")
        self.image.save()
        self.image.renditions.all().delete()
        new_rendition = self.image.get_rendition("width-500")
        self.assertFalse(hasattr(new_rendition, "_mark"))

    def test_prefers_rendition_cache_backend(self):
        with override_settings(
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                },
                "renditions": {
                    "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                },
            }
        ):
            self.assertEqual(Rendition.cache_backend, caches["renditions"])

    def test_uses_default_cache_when_no_renditions_cache(self):
        with override_settings(
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.dummy.DummyCache",
                }
            }
        ):
            self.assertEqual(Rendition.cache_backend, caches["default"])

    def test_focal_point(self):
        self.image.focal_point_x = 100
        self.image.focal_point_y = 200
        self.image.focal_point_width = 50
        self.image.focal_point_height = 20
        self.image.save()

        # Generate a rendition that's half the size of the original
        rendition = self.image.get_rendition("width-320")

        self.assertEqual(rendition.focal_point.round(), Rect(37, 95, 63, 105))
        self.assertEqual(rendition.focal_point.centroid.x, 50)
        self.assertEqual(rendition.focal_point.centroid.y, 100)
        self.assertEqual(rendition.focal_point.width, 25)
        self.assertEqual(rendition.focal_point.height, 10)

        self.assertEqual(
            rendition.background_position_style, "background-position: 15% 41%;"
        )

    def test_background_position_style_default(self):
        # Generate a rendition that's half the size of the original
        rendition = self.image.get_rendition("width-320")

        self.assertEqual(
            rendition.background_position_style, "background-position: 50% 50%;"
        )

    def test_custom_rendition_backend_setting(self):
        """
        Test the usage of WAGTAILIMAGES_RENDITION_STORAGE setting.
        """
        # when setting is not set, instance.get_storage() returns DefaultStorage
        from django.conf import settings

        bkp = settings

        self.assertFalse(hasattr(settings, "WAGTAILIMAGES_RENDITION_STORAGE"))
        rendition1 = self.image.get_rendition("min-120x120")
        self.assertIsInstance(rendition1.image.file.storage, DefaultStorage)

        # when setting is set to a path
        setattr(
            settings,
            "WAGTAILIMAGES_RENDITION_STORAGE",
            "wagtail.images.tests.test_models.CustomStorage",
        )
        backend = get_rendition_storage()
        self.assertIsInstance(backend, CustomStorage)

        # when setting is set directly, get_rendition_storage() returns the custom storage backend
        class CustomStorage2(Storage):
            def __init__(self):
                super().__init__()

        setattr(settings, "WAGTAILIMAGES_RENDITION_STORAGE", CustomStorage2())
        backend = get_rendition_storage()
        self.assertIsInstance(backend, CustomStorage2)

        # clean up
        settings = bkp


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class TestPrefetchRenditions(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.images = []
        self.event_pages_pks = []

        event_pages = EventPage.objects.all()[:3]
        for i, page in enumerate(event_pages):
            page.feed_image = image = Image.objects.create(
                title="Test image {i}",
                file=get_test_image_file(),
            )
            page.save(update_fields=["feed_image"])
            self.images.append(image)
            self.event_pages_pks.append(page.pk)

        # Generate renditions
        self.small_renditions = [
            image.get_rendition("max-100x100") for image in self.images
        ]
        self.large_renditions = [
            image.get_rendition("min-300x600") for image in self.images
        ]

    def test_prefetch_renditions_on_non_image_querysets(self):
        prefetch_images_and_small_renditions = Prefetch(
            "feed_image", queryset=Image.objects.prefetch_renditions("max-100x100")
        )
        with self.assertNumQueries(3):
            # One query to get the `EventPage`s, another one to fetch the feed images
            # and a last one to select matching renditions.
            pages = list(
                EventPage.objects.prefetch_related(
                    prefetch_images_and_small_renditions
                ).filter(pk__in=self.event_pages_pks)
            )

        with self.assertNumQueries(0):
            # No additional query since small renditions were prefetched.
            small_renditions = [
                page.feed_image.get_rendition("max-100x100") for page in pages
            ]

        self.assertListEqual(self.small_renditions, small_renditions)

        with self.assertNumQueries(3):
            # Additional queries since large renditions weren't prefetched.
            large_renditions = [
                page.feed_image.get_rendition("min-300x600") for page in pages
            ]

        self.assertListEqual(self.large_renditions, large_renditions)


class TestUsageCount(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_unused_image_usage_count(self):
        self.assertEqual(self.image.get_usage().count(), 0)

    def test_used_image_document_usage_count(self):
        page = EventPage.objects.get(id=4)
        event_page_carousel_item = EventPageCarouselItem()
        event_page_carousel_item.page = page
        event_page_carousel_item.image = self.image
        event_page_carousel_item.save()
        self.assertEqual(self.image.get_usage().count(), 1)


class TestGetUsage(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_unused_image_get_usage(self):
        self.assertEqual(list(self.image.get_usage()), [])

    def test_used_image_document_get_usage(self):
        page = EventPage.objects.get(id=4)
        event_page_carousel_item = EventPageCarouselItem()
        event_page_carousel_item.page = page
        event_page_carousel_item.image = self.image
        event_page_carousel_item.save()

        self.assertIsInstance(self.image.get_usage()[0], tuple)
        self.assertIsInstance(self.image.get_usage()[0][0], Page)
        self.assertIsInstance(self.image.get_usage()[0][1], list)
        self.assertIsInstance(self.image.get_usage()[0][1][0], ReferenceIndex)


class TestGetWillowImage(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_willow_image_object_returned(self):
        with self.image.get_willow_image() as willow_image:
            self.assertIsInstance(willow_image, WillowImage)

    def test_with_missing_image(self):
        # Image id=1 in test fixtures has a missing image file
        bad_image = Image.objects.get(id=1)

        # Attempting to get the Willow image for images without files
        # should raise a SourceImageIOError
        with self.assertRaises(SourceImageIOError):
            with bad_image.get_willow_image():
                self.fail()  # Shouldn't get here

    def test_closes_image(self):
        # This tests that willow closes images after use
        with self.image.get_willow_image():
            self.assertFalse(self.image.file.closed)

        self.assertTrue(self.image.file.closed)

    def test_closes_image_on_exception(self):
        # This tests that willow closes images when the with is exited with an exception
        try:
            with self.image.get_willow_image():
                self.assertFalse(self.image.file.closed)
                raise ValueError("Something went wrong!")
        except ValueError:
            pass

        self.assertTrue(self.image.file.closed)

    def test_doesnt_close_open_image(self):
        # This tests that when the image file is already open, get_willow_image doesn't close it (#1256)
        self.image.file.open("rb")

        with self.image.get_willow_image():
            pass

        self.assertFalse(self.image.file.closed)

        self.image.file.close()


class TestIssue573(TestCase):
    """
    This tests for a bug which causes filename limit on Renditions to be reached
    when the Image has a long original filename and a big focal point key
    """

    def test_issue_573(self):
        # Create an image with a big filename and focal point
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(
                "thisisaverylongfilename-cdefghijklmnopqrstuvwxyzab-supercalifragilisticexpialidocious.png"
            ),
            focal_point_x=1000,
            focal_point_y=1000,
            focal_point_width=1000,
            focal_point_height=1000,
        )

        # Try creating a rendition from that image
        # This would crash if the bug is present
        image.get_rendition("fill-800x600")


@override_settings(_WAGTAILSEARCH_FORCE_AUTO_UPDATE=["elasticsearch"])
class TestIssue613(WagtailTestUtils, TestCase):
    def get_elasticsearch_backend(self):
        from django.conf import settings

        from wagtail.search.backends import get_search_backend

        if "elasticsearch" not in settings.WAGTAILSEARCH_BACKENDS:
            raise unittest.SkipTest("No elasticsearch backend active")

        return get_search_backend("elasticsearch")

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_image(self, **params):
        post_data = {
            "title": "Test image",
            "file": SimpleUploadedFile(
                "test.png", get_test_image_file().file.getvalue()
            ),
        }
        post_data.update(params)
        response = self.client.post(reverse("wagtailimages:add"), post_data)

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

        return image

    def edit_image(self, **params):
        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Edit it
        post_data = {
            "title": "Edited",
        }
        post_data.update(params)
        response = self.client.post(
            reverse("wagtailimages:edit", args=(self.image.id,)), post_data
        )

        # Should redirect back to index
        self.assertRedirects(response, reverse("wagtailimages:index"))

        # Check that the image was edited
        image = Image.objects.get(id=self.image.id)
        self.assertEqual(image.title, "Edited")
        return image

    def test_issue_613_on_add(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(Image)

        # Add an image with some tags
        image = self.add_image(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", Image)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, image.id)

    def test_issue_613_on_edit(self):
        # Reset the search index
        self.search_backend.reset_index()
        self.search_backend.add_type(Image)

        # Add an image with some tags
        image = self.edit_image(tags="hello")
        self.search_backend.refresh_index()

        # Search for it by tag
        results = self.search_backend.search("hello", Image)

        # Check
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, image.id)


class TestIssue312(TestCase):
    def test_duplicate_renditions(self):
        # Create an image
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Get two renditions and check that they're the same
        rend1 = image.get_rendition("fill-100x100")
        rend2 = image.get_rendition("fill-100x100")
        self.assertEqual(rend1, rend2)

        # Now manually duplicate the renditon and check that the database blocks it
        self.assertRaises(
            IntegrityError,
            Rendition.objects.create,
            image=rend1.image,
            filter_spec=rend1.filter_spec,
            width=rend1.width,
            height=rend1.height,
            focal_point_key=rend1.focal_point_key,
        )


class TestFilenameReduction(TestCase):
    """
    This tests for a bug which results in filenames without extensions
    causing an infinite loop
    """

    def test_filename_reduction_no_ext(self):
        # Create an image with a big filename and no extension
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(
                "thisisaverylongfilename-defghijklmnopqrstuvwxyzabc-supercalifragilisticexpialidocioussuperlong"
            ),
        )

        # Saving file will result in infinite loop when bug is present
        image.save()
        self.assertEqual(
            "original_images/thisisaverylongfilename-defghijklmnopqrstuvwxyzabc-supercalifragilisticexpiali",
            image.file.name,
        )

    # Test for happy path. Long filename with extension
    def test_filename_reduction_ext(self):
        # Create an image with a big filename and extensions
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(
                "thisisaverylongfilename-efghijklmnopqrstuvwxyzabcd-supercalifragilisticexpialidocioussuperlong.png"
            ),
        )

        image.save()
        self.assertEqual(
            "original_images/thisisaverylongfilename-efghijklmnopqrstuvwxyzabcd-supercalifragilisticexp.png",
            image.file.name,
        )


class TestRenditionOrientation(TestCase):
    """
    This tests for a bug where images with exif orientations which
    required rotation for display were cropped and sized based on the
    unrotated image dimensions.

    For example images with specified dimensions of 640x450 but an exif orientation of 6
    should appear as a 450x640 portrait, but instead were still cropped to 640x450.

    Actual image files are used so that exif orientation data will exist for the rotation to function correctly.
    """

    def assert_orientation_landscape_image_is_correct(self, rendition):
        """
        Check that the image has the correct colored pixels in the right places
        so that we know the image did not physically rotate.
        """

        from willow.plugins.pillow import PillowImage

        with rendition.get_willow_image() as willow_image:
            image = PillowImage.open(willow_image)
        # Check that the image is the correct size (and not rotated)
        self.assertEqual(image.get_size(), (600, 450))
        # Check that the red flower is in the bottom left
        # The JPEGs have compressed slightly differently so the colours won't be spot on
        colour = image.image.convert("RGB").getpixel((155, 282))
        self.assertAlmostEqual(colour[0], 217, delta=25)
        self.assertAlmostEqual(colour[1], 38, delta=25)
        self.assertAlmostEqual(colour[2], 46, delta=25)

        # Check that the water is at the bottom
        colour = image.image.convert("RGB").getpixel((377, 434))
        self.assertAlmostEqual(colour[0], 85, delta=25)
        self.assertAlmostEqual(colour[1], 93, delta=25)
        self.assertAlmostEqual(colour[2], 65, delta=25)

    def test_jpeg_with_orientation_1(self):
        with open("wagtail/images/tests/image_files/landscape_1.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 600)
        self.assertEqual(image.height, 450)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_2(self):
        with open("wagtail/images/tests/image_files/landscape_2.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 600)
        self.assertEqual(image.height, 450)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_3(self):
        with open("wagtail/images/tests/image_files/landscape_3.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 600)
        self.assertEqual(image.height, 450)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_4(self):
        with open("wagtail/images/tests/image_files/landscape_4.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 600)
        self.assertEqual(image.height, 450)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    # tests below here have a specified width x height in portrait but
    # an orientation specified of landscape, so the original shows a height > width
    # but the rendition is corrected to height < width.
    def test_jpeg_with_orientation_5(self):
        with open("wagtail/images/tests/image_files/landscape_6.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 450)
        self.assertEqual(image.height, 600)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_6(self):
        with open("wagtail/images/tests/image_files/landscape_6.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 450)
        self.assertEqual(image.height, 600)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_7(self):
        with open("wagtail/images/tests/image_files/landscape_7.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 450)
        self.assertEqual(image.height, 600)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)

    def test_jpeg_with_orientation_8(self):
        with open("wagtail/images/tests/image_files/landscape_8.jpg", "rb") as f:
            image = Image.objects.create(title="Test image", file=File(f))

        # check preconditions
        self.assertEqual(image.width, 450)
        self.assertEqual(image.height, 600)
        rendition = image.get_rendition("original")
        # Check dimensions stored on the model
        self.assertEqual(rendition.width, 600)
        self.assertEqual(rendition.height, 450)
        # Check actual image dimensions and orientation
        self.assert_orientation_landscape_image_is_correct(rendition)
