import json
import datetime

from mock import MagicMock
import dateutil.parser

from django.utils import six
from django.utils.http import urlquote
from django.utils import timezone
from django.test import TestCase
from django import template
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail.tests.utils import unittest, WagtailTestUtils
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailimages.formats import (
    Format,
    get_image_format,
    register_image_format
)

from wagtail.wagtailimages.backends import get_image_backend
from wagtail.wagtailimages.backends.pillow import PillowBackend
from wagtail.wagtailimages.utils.crop import crop_to_point, CropBox
from wagtail.wagtailimages.utils.focal_point import FocalPoint
from wagtail.wagtailimages.utils.crypto import generate_signature, verify_signature


def get_test_image_file():
    from six import BytesIO
    from PIL import Image
    from django.core.files.images import ImageFile

    f = BytesIO()
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


class TestImageTag(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def render_image_tag(self, image, filter_spec):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj ' + filter_spec + '%}')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag(self):
        result = self.render_image_tag(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def render_image_tag_as(self, image, filter_spec):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj ' + filter_spec + ' as test_img %}<img {{ test_img.attrs }} />')
        context = template.Context({'image_obj': image})
        return temp.render(context)

    def test_image_tag_attrs(self):
        result = self.render_image_tag_as(self.image, 'width-400')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def render_image_tag_with_extra_attributes(self, image, title):
        temp = template.Template('{% load wagtailimages_tags %}{% image image_obj width-400 class="photo" title=title|lower %}')
        context = template.Context({'image_obj': image, 'title': title})
        return temp.render(context)

    def test_image_tag_with_extra_attributes(self):
        result = self.render_image_tag_with_extra_attributes(self.image, 'My Wonderful Title')

        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('class="photo"' in result)
        self.assertTrue('title="my wonderful title"' in result)

## ===== ADMIN VIEWS =====


class TestImageIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/index.html')

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


class TestImageAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_add_image'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_add_image'), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

    def test_add(self):
        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages_index'))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)


class TestImageEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_edit_image', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_edit_image', args=(self.image.id,)), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')

    def test_edit(self):
        response = self.post({
            'title': "Edited",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages_index'))

        # Check that the image was edited
        image = Image.objects.get(id=self.image.id)
        self.assertEqual(image.title, "Edited")


class TestImageDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_delete_image', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages_delete_image', args=(self.image.id,)), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/confirm_delete.html')

    def test_delete(self):
        response = self.post({
            'hello': 'world'
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages_index'))

        # Check that the image was deleted
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 0)


class TestImageChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.js')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestImageChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_image_chosen', args=(self.image.id,)), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/image_chosen.js')

    # TODO: Test posting


class TestImageChooserUploadView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser_upload'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.js')

    # TODO: Test uploading through chooser


class TestFormat(TestCase):
    def setUp(self):
        # test format
        self.format = Format(
            'test name',
            'test label',
            'test classnames',
            'test filter spec'
        )
        # test image
        self.image = MagicMock()
        self.image.id = 0

    def test_editor_attributes(self):
        result = self.format.editor_attributes(
            self.image,
            'test alt text'
        )
        self.assertEqual(result,
                         'data-embedtype="image" data-id="0" data-format="test name" data-alt="test alt text" ')

    def test_image_to_editor_html(self):
        result = self.format.image_to_editor_html(
            self.image,
            'test alt text'
        )
        six.assertRegex(self, result,
            '<img data-embedtype="image" data-id="0" data-format="test name" data-alt="test alt text" class="test classnames" src="[^"]+" width="1" height="1" alt="test alt text">',
        )

    def test_image_to_html_no_classnames(self):
        self.format.classnames = None
        result = self.format.image_to_html(self.image, 'test alt text')
        six.assertRegex(self, result,
            '<img src="[^"]+" width="1" height="1" alt="test alt text">'
        )
        self.format.classnames = 'test classnames'

    def test_get_image_format(self):
        register_image_format(self.format)
        result = get_image_format('test name')
        self.assertEqual(result, self.format)


class TestMultipleImageUploader(TestCase, WagtailTestUtils):
    """
    This tests the multiple image upload views located in wagtailimages/views/multiple.py
    """
    def setUp(self):
        self.login()

        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_add(self):
        """
        This tests that the add view responds correctly on a GET request
        """
        # Send request
        response = self.client.get(reverse('wagtailimages_add_multiple'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/multiple/add.html')

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the image and returns an edit form
        """
        response = self.client.post(reverse('wagtailimages_add_multiple'), {
            'files[]': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtailimages/multiple/edit_form.html')

        # Check image
        self.assertIn('image', response.context)
        self.assertEqual(response.context['image'].title, 'test.png')

        # Check form
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].initial['title'], 'test.png')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('image_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['image_id'], response.context['image'].id)
        self.assertTrue(response_json['success'])

    def test_add_post_noajax(self):
        """
        This tests that only AJAX requests are allowed to POST to the add view
        """
        response = self.client.post(reverse('wagtailimages_add_multiple'), {})

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_nofile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse('wagtailimages_add_multiple'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_badfile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse('wagtailimages_add_multiple'), {
            'files[]': SimpleUploadedFile('test.png', b"This is not an image!"),
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertNotIn('image_id', response_json)
        self.assertNotIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertIn('error_message', response_json)
        self.assertFalse(response_json['success'])
        self.assertEqual(response_json['error_message'], 'Not a valid image. Please use a gif, jpeg or png file with the correct file extension (*.gif, *.jpg or *.png).')

    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtailimages_edit_multiple', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the image
        """
        # Send request
        response = self.client.post(reverse('wagtailimages_edit_multiple', args=(self.image.id, )), {
            ('image-%d-title' % self.image.id): "New title!",
            ('image-%d-tags' % self.image.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('image_id', response_json)
        self.assertNotIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['image_id'], self.image.id)
        self.assertTrue(response_json['success'])

    def test_edit_post_noajax(self):
        """
        This tests that a POST request to the edit view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtailimages_edit_multiple', args=(self.image.id, )), {
            ('image-%d-title' % self.image.id): "New title!",
            ('image-%d-tags' % self.image.id): "",
        })

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_edit_post_validation_error(self):
        """
        This tests that a POST request to the edit page returns a json document with "success=False"
        and a form with the validation error indicated
        """
        # Send request
        response = self.client.post(reverse('wagtailimages_edit_multiple', args=(self.image.id, )), {
            ('image-%d-title' % self.image.id): "", # Required
            ('image-%d-tags' % self.image.id): "",
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtailimages/multiple/edit_form.html')

        # Check that a form error was raised
        self.assertFormError(response, 'form', 'title', "This field is required.")

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('image_id', response_json)
        self.assertIn('form', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['image_id'], self.image.id)
        self.assertFalse(response_json['success'])

    def test_delete_get(self):
        """
        This tests that a GET request to the delete view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtailimages_delete_multiple', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the image
        """
        # Send request
        response = self.client.post(reverse('wagtailimages_delete_multiple', args=(self.image.id, )), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Make sure the image is deleted
        self.assertFalse(Image.objects.filter(id=self.image.id).exists())

        # Check JSON
        response_json = json.loads(response.content.decode())
        self.assertIn('image_id', response_json)
        self.assertIn('success', response_json)
        self.assertEqual(response_json['image_id'], self.image.id)
        self.assertTrue(response_json['success'])

    def test_edit_post_noajax(self):
        """
        This tests that a POST request to the delete view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtailimages_delete_multiple', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestSignatureGeneration(TestCase):
    def test_signature_generation(self):
        self.assertEqual(generate_signature(100, 'fill-800x600'), b'xnZOzQyUg6pkfciqcfRJRosOrGg=')

    def test_signature_verification(self):
        self.assertTrue(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 100, 'fill-800x600'))

    def test_signature_changes_on_image_id(self):
        self.assertFalse(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 200, 'fill-800x600'))

    def test_signature_changes_on_filter_spec(self):
        self.assertFalse(verify_signature(b'xnZOzQyUg6pkfciqcfRJRosOrGg=', 100, 'fill-800x700'))


class TestFrontendServeView(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def test_get(self):
        """
        Test a valid GET request to the view
        """
        # Generate signature
        signature = generate_signature(self.image.id, 'fill-800x600')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

        # Make sure the cache headers are set to expire after at least one month
        self.assertIn('Cache-Control', response)
        self.assertEqual(response['Cache-Control'].split('=')[0], 'max-age')
        self.assertTrue(int(response['Cache-Control'].split('=')[1]) > datetime.timedelta(days=30).seconds)

        self.assertIn('Expires', response)
        self.assertTrue(dateutil.parser.parse(response['Expires']) > timezone.now() + datetime.timedelta(days=30))

    def test_get_invalid_signature(self):
        """
        Test that an invalid signature returns a 403 response
        """
        # Generate a signature for the incorrect image id
        signature = generate_signature(self.image.id + 1, 'fill-800x600')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 403)

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Generate a signature with the invalid filterspec
        signature = generate_signature(self.image.id, 'bad-filter-spec')

        # Get the image
        response = self.client.get(reverse('wagtailimages_serve', args=(signature, self.image.id, 'bad-filter-spec')))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestURLGeneratorView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Login
        self.user = self.login()

    def test_get(self):
        """
        This tests that the view responds correctly for a user with edit permissions on this image
        """
        # Get
        response = self.client.get(reverse('wagtailimages_url_generator', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/url_generator.html')

    def test_get_bad_permissions(self):
        """
        This tests that the view gives a 403 if a user without correct permissions attemts to access it
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get
        response = self.client.get(reverse('wagtailimages_url_generator', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 403)


class TestGenerateURLView(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Login
        self.user = self.login()

    def test_get(self):
        """
        This tests that the view responds correctly for a user with edit permissions on this image
        """
        # Get
        response = self.client.get(reverse('wagtailimages_generate_url', args=(self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        content_json = json.loads(response.content.decode())

        self.assertEqual(set(content_json.keys()), set(['url', 'local_url']))

        expected_url = 'http://localhost/images/%(signature)s/%(image_id)d/fill-800x600/' % {
            'signature': urlquote(generate_signature(self.image.id, 'fill-800x600').decode()),
            'image_id': self.image.id,
        }
        self.assertEqual(content_json['url'], expected_url)

        expected_local_url = '/images/%(signature)s/%(image_id)d/fill-800x600/' % {
            'signature': urlquote(generate_signature(self.image.id, 'fill-800x600').decode()),
            'image_id': self.image.id,
        }
        self.assertEqual(content_json['local_url'], expected_local_url)

    def test_get_bad_permissions(self):
        """
        This tests that the view gives a 403 if a user without correct permissions attemts to access it
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get
        response = self.client.get(reverse('wagtailimages_generate_url', args=(self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        self.assertJSONEqual(response.content.decode(), json.dumps({
            'error': 'You do not have permission to generate a URL for this image.',
        }))

    def test_get_bad_image(self):
        """
        This tests that the view gives a 404 response if a user attempts to use it with an image which doesn't exist
        """
        # Get
        response = self.client.get(reverse('wagtailimages_generate_url', args=(self.image.id + 1, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        self.assertJSONEqual(response.content.decode(), json.dumps({
            'error': 'Cannot find image.',
        }))

    def test_get_bad_filter_spec(self):
        """
        This tests that the view gives a 400 response if the user attempts to use it with an invalid filter spec
        """
        # Get
        response = self.client.get(reverse('wagtailimages_generate_url', args=(self.image.id, 'bad-filter-spec')))

        # Check response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        self.assertJSONEqual(response.content.decode(), json.dumps({
            'error': 'Invalid filter spec.',
        }))


class TestCropToPoint(TestCase):
    def test_basic(self):
        "Test basic cropping in the centre of the image"
        self.assertEqual(
            crop_to_point((640, 480), (100, 100), FocalPoint(x=320, y=240)),
            CropBox(270, 190, 370, 290),
        )
        
    def test_basic_no_focal_point(self):
        "If focal point is None, it should make one in the centre of the image"
        self.assertEqual(
            crop_to_point((640, 480), (100, 100), None),
            CropBox(270, 190, 370, 290),
        )

    def test_doesnt_exit_top_left(self):
        "Test that the cropbox doesn't exit the image at the top left"
        self.assertEqual(
            crop_to_point((640, 480), (100, 100), FocalPoint(x=0, y=0)),
            CropBox(0, 0, 100, 100),
        )

    def test_doesnt_exit_bottom_right(self):
        "Test that the cropbox doesn't exit the image at the bottom right"
        self.assertEqual(
            crop_to_point((640, 480), (100, 100), FocalPoint(x=640, y=480)),
            CropBox(540, 380, 640, 480),
        )

    def test_doesnt_get_smaller_than_focal_point(self):
        "Test that the cropbox doesn't get any smaller than the focal point"
        self.assertEqual(
            crop_to_point((640, 480), (10, 10), FocalPoint(x=320, y=240, width=100, height=100)),
            CropBox(270, 190, 370, 290),
        )

    def test_keeps_composition(self):
        "Test that the cropbox tries to keep the composition of the original image as much as it can"
        self.assertEqual(
            crop_to_point((300, 300), (150, 150), FocalPoint(x=100, y=200)),
            CropBox(50, 100, 200, 250), # Focal point is 1/3 across and 2/3 down in the crop box
        )

    def test_keeps_focal_point_in_view_bottom_left(self):
        """
        Even though it tries to keep the composition of the image,
        it shouldn't let that get in the way of keeping the entire subject in view
        """
        self.assertEqual(
            crop_to_point((300, 300), (150, 150), FocalPoint(x=100, y=200, width=150, height=150)),
            CropBox(25, 125, 175, 275),
        )

    def test_keeps_focal_point_in_view_top_right(self):
        """
        Even though it tries to keep the composition of the image,
        it shouldn't let that get in the way of keeping the entire subject in view
        """
        self.assertEqual(
            crop_to_point((300, 300), (150, 150), FocalPoint(x=200, y=100, width=150, height=150)),
            CropBox(125, 25, 275, 175),
        )

