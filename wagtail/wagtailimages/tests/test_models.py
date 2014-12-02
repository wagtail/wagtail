from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.db import connection

from wagtail.tests.utils import WagtailTestUtils, unittest, test_concurrently
from wagtail.wagtailcore.models import Page
from wagtail.tests.models import EventPage, EventPageCarouselItem
from wagtail.wagtailimages.models import Rendition, Filter
from wagtail.wagtailimages.backends import get_image_backend
from wagtail.wagtailimages.backends.pillow import PillowBackend
from wagtail.wagtailimages.rect import Rect

from .utils import Image, get_test_image_file


class TestImage(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_is_portrait(self):
        self.assertFalse(self.image.is_portrait())

    def test_is_landscape(self):
        self.assertTrue(self.image.is_landscape())

    def test_get_rect(self):
        self.assertTrue(self.image.get_rect(), Rect(0, 0, 640, 480))

    def test_get_focal_point(self):
        self.assertEqual(self.image.get_focal_point(), None)

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
        self.assertEqual(self.image.focal_point_x, None)
        self.assertEqual(self.image.focal_point_y, None)
        self.assertEqual(self.image.focal_point_width, None)
        self.assertEqual(self.image.focal_point_height, None)

        self.image.set_focal_point(Rect(100, 150, 200, 350))

        self.assertEqual(self.image.focal_point_x, 150)
        self.assertEqual(self.image.focal_point_y, 250)
        self.assertEqual(self.image.focal_point_width, 100)
        self.assertEqual(self.image.focal_point_height, 200)

        self.image.set_focal_point(None)

        self.assertEqual(self.image.focal_point_x, None)
        self.assertEqual(self.image.focal_point_y, None)
        self.assertEqual(self.image.focal_point_width, None)
        self.assertEqual(self.image.focal_point_height, None)


class TestImagePermissions(TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
        User = get_user_model()
        self.user = User.objects.create_user(username='user', email='user@email.com', password='password')
        self.owner = User.objects.create_user(username='owner', email='owner@email.com', password='password')
        self.editor = User.objects.create_user(username='editor', email='editor@email.com', password='password')
        self.editor.groups.add(Group.objects.get(name='Editors'))
        self.administrator = User.objects.create_superuser(username='administrator', email='administrator@email.com', password='password')

        # Owner user must have the add_image permission
        self.owner.user_permissions.add(Permission.objects.get(codename='add_image'))

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


class TestRenditions(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_default_backend(self):
        # default backend should be pillow
        backend = get_image_backend()
        self.assertTrue(isinstance(backend, PillowBackend))

    def test_minification(self):
        rendition = self.image.get_rendition('width-400')

        # Check size
        self.assertEqual(rendition.width, 400)
        self.assertEqual(rendition.height, 300)

    def test_resize_to_max(self):
        rendition = self.image.get_rendition('max-100x100')

        # Check size
        self.assertEqual(rendition.width, 100)
        self.assertEqual(rendition.height, 75)


    def test_resize_to_min(self):
        rendition = self.image.get_rendition('min-120x120')

        # Check size
        self.assertEqual(rendition.width, 160)
        self.assertEqual(rendition.height, 120)

    def test_resize_to_original(self):
        rendition = self.image.get_rendition('original')

        # Check size
        self.assertEqual(rendition.width, 640)
        self.assertEqual(rendition.height, 480)

    def test_cache(self):
        # Get two renditions with the same filter
        first_rendition = self.image.get_rendition('width-400')
        second_rendition = self.image.get_rendition('width-400')

        # Check that they are the same object
        self.assertEqual(first_rendition, second_rendition)


class TestRenditionsWand(TestCase):
    def setUp(self):
        try:
            import wand
        except ImportError:
            # skip these tests if Wand is not installed
            raise unittest.SkipTest(
                "Skipping image backend tests for wand, as wand is not installed")

        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.image.backend = 'wagtail.wagtailimages.backends.wand.WandBackend'

    def test_minification(self):
        rendition = self.image.get_rendition('width-400')

        # Check size
        self.assertEqual(rendition.width, 400)
        self.assertEqual(rendition.height, 300)

    def test_resize_to_max(self):
        rendition = self.image.get_rendition('max-100x100')

        # Check size
        self.assertEqual(rendition.width, 100)
        self.assertEqual(rendition.height, 75)

    def test_resize_to_min(self):
        rendition = self.image.get_rendition('min-120x120')

        # Check size
        self.assertEqual(rendition.width, 160)
        self.assertEqual(rendition.height, 120)

    def test_resize_to_original(self):
        rendition = self.image.get_rendition('original')

        # Check size
        self.assertEqual(rendition.width, 640)
        self.assertEqual(rendition.height, 480)

    def test_cache(self):
        # Get two renditions with the same filter
        first_rendition = self.image.get_rendition('width-400')
        second_rendition = self.image.get_rendition('width-400')

        # Check that they are the same object
        self.assertEqual(first_rendition, second_rendition)


class TestUsageCount(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_image_usage_count(self):
        self.assertEqual(self.image.get_usage().count(), 0)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_image_document_usage_count(self):
        page = EventPage.objects.get(id=4)
        event_page_carousel_item = EventPageCarouselItem()
        event_page_carousel_item.page = page
        event_page_carousel_item.image = self.image
        event_page_carousel_item.save()
        self.assertEqual(self.image.get_usage().count(), 1)


class TestGetUsage(TestCase):
    fixtures = ['wagtail/tests/fixtures/test.json']

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_image_get_usage_not_enabled(self):
        self.assertEqual(list(self.image.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_unused_image_get_usage(self):
        self.assertEqual(list(self.image.get_usage()), [])

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_used_image_document_get_usage(self):
        page = EventPage.objects.get(id=4)
        event_page_carousel_item = EventPageCarouselItem()
        event_page_carousel_item.page = page
        event_page_carousel_item.image = self.image
        event_page_carousel_item.save()
        self.assertTrue(issubclass(Page, type(self.image.get_usage()[0])))


class TestIssue573(TestCase):
    """
    This tests for a bug which causes filename limit on Renditions to be reached
    when the Image has a long original filename and a big focal point key
    """
    def test_issue_573(self):
        # Create an image with a big filename and focal point
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file('thisisaverylongfilename-abcdefghijklmnopqrstuvwxyz-supercalifragilisticexpialidocious.png'),
            focal_point_x=1000,
            focal_point_y=1000,
            focal_point_width=1000,
            focal_point_height=1000,
        )

        # Try creating a rendition from that image
        # This would crash if the bug is present
        image.get_rendition('fill-800x600')


class TestIssue613(TestCase, WagtailTestUtils):
    def get_elasticsearch_backend(self):
        from django.conf import settings
        from wagtail.wagtailsearch.backends import get_search_backend

        backend_path = 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch'

        # Search WAGTAILSEARCH_BACKENDS for an entry that uses the given backend path
        for backend_name, backend_conf in settings.WAGTAILSEARCH_BACKENDS.items():
            if backend_conf['BACKEND'] == backend_path:
                return get_search_backend(backend_name)
        else:
            # no conf entry found - skip tests for this backend
            raise unittest.SkipTest("No WAGTAILSEARCH_BACKENDS entry for the backend %s" % backend_path)

    def setUp(self):
        self.search_backend = self.get_elasticsearch_backend()
        self.login()

    def add_image(self, **params):
        post_data = {
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtailimages_add_image'), post_data)

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages_index'))

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
            'title': "Edited",
        }
        post_data.update(params)
        response = self.client.post(reverse('wagtailimages_edit_image', args=(self.image.id,)), post_data)

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages_index'))

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
        rend1 = image.get_rendition('fill-100x100')
        rend2 = image.get_rendition('fill-100x100')
        self.assertEqual(rend1, rend2)

        # Now manually duplicate the renditon and check that the database blocks it
        self.assertRaises(
            IntegrityError,
            Rendition.objects.create, 
            image=rend1.image,
            filter=rend1.filter,
            width=rend1.width,
            height=rend1.height,
            focal_point_key=rend1.focal_point_key,
        )

    def test_duplicate_filters(self):
        @test_concurrently(10)
        def get_renditions():
            # Create an image
            image = Image.objects.create(
                title="Concurrency test image",
                file=get_test_image_file(),
            )
            # get renditions concurrently, using various filters that are unlikely to exist already
            for width in range(10, 100, 10):
                image.get_rendition('width-%d' % width)

            # this block opens multiple database connections, which need to be closed explicitly
            # so that we can drop the test database at the end of the test run
            connection.close()

        get_renditions()
        # if the above has completed with no race conditions, there should be precisely one
        # of each of the above filters in the database
        for width in range(10, 100, 10):
            self.assertEqual(Filter.objects.filter(spec='width-%d' % width).count(), 1)
