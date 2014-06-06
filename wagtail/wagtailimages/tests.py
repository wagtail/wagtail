from django.test import TestCase
from django import template
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail.tests.utils import login, unittest
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.templatetags import image_tags

from wagtail.wagtailimages.backends import get_image_backend
from wagtail.wagtailimages.backends.pillow import PillowBackend

def get_test_image_file():
    from StringIO import StringIO
    from PIL import Image
    from django.core.files.images import ImageFile

    f = StringIO()
    image = Image.new('RGB', (640, 480), 'white')
    image.save(f, 'PNG')
    return ImageFile(f, name='test.png')


Image = get_image_model()


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


class TestImagePermissions(TestCase):
    def setUp(self):
        # Create some user accounts for testing permissions
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

    def test_cache(self):
        # Get two renditions with the same filter
        first_rendition = self.image.get_rendition('width-400')
        second_rendition = self.image.get_rendition('width-400')

        # Check that they are the same object
        self.assertEqual(first_rendition, second_rendition)
        

class TestImageTag(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def render_image_tag(self, image, filter_spec):
        temp = template.Template('{% load image_tags %}{% image image_obj ' + filter_spec + '%}')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag(self):
        result = self.render_image_tag(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def render_image_tag_as(self, image, filter_spec):
        temp = template.Template('{% load image_tags %}{% image image_obj ' + filter_spec + ' as test_img %}<img {{ test_img.attrs }} />')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag_attrs(self):
        result = self.render_image_tag_as(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

## ===== ADMIN VIEWS =====


class TestImageIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_index'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.get({'ordering': ordering})
            self.assertEqual(response.status_code, 200)


class TestImageAddView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_add_image'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_add_image'), post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_add(self):
        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)


class TestImageEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_edit_image', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_edit_image', args=(self.image.id,)), post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_edit(self):
        response = self.post({
            'title': "Edited",
        })

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the image was edited
        image = Image.objects.get(id=self.image.id)
        self.assertEqual(image.title, "Edited")


class TestImageDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_delete_image', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_delete_image', args=(self.image.id,)), post_data)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_delete(self):
        response = self.post({
            'hello': 'world'
        })

        # Should redirect back to index
        self.assertEqual(response.status_code, 302)

        # Check that the image was deleted
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 0)


class TestImageChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestImageChooserChosenView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_image_chosen', args=(self.image.id,)), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestImageChooserUploadView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser_upload'), params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
