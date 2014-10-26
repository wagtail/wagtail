import json

from django.test import TestCase
from django.utils.http import urlquote
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailimages.utils import generate_signature

from .utils import Image, get_test_image_file


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

    def test_add_no_file_selected(self):
        response = self.post({
            'title': "Test image",
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # The form should have an error
        self.assertFormError(response, 'form', 'file', "This field is required.")


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

    def test_upload(self):
        response = self.client.post(reverse('wagtailimages_chooser_upload'), {
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

    def test_upload_no_file_selected(self):
        response = self.client.post(reverse('wagtailimages_chooser_upload'), {
            'title': "Test image",
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

        # The form should have an error
        self.assertFormError(response, 'uploadform', 'file', "This field is required.")


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
        self.assertEqual(response_json['error_message'], "Not a supported image format. Supported formats: GIF, JPEG, PNG.")

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

        self.assertEqual(set(content_json.keys()), set(['url', 'preview_url']))

        expected_url = 'http://localhost/images/%(signature)s/%(image_id)d/fill-800x600/' % {
            'signature': urlquote(generate_signature(self.image.id, 'fill-800x600').decode()),
            'image_id': self.image.id,
        }
        self.assertEqual(content_json['url'], expected_url)

        expected_preview_url = reverse('wagtailimages_preview', args=(self.image.id, 'fill-800x600'))
        self.assertEqual(content_json['preview_url'], expected_preview_url)

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


class TestPreviewView(TestCase, WagtailTestUtils):
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
        Test a valid GET request to the view
        """
        # Get the image
        response = self.client.get(reverse('wagtailimages_preview', args=(self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Get the image
        response = self.client.get(reverse('wagtailimages_preview', args=(self.image.id, 'bad-filter-spec')))

        # Check response
        self.assertEqual(response.status_code, 400)
