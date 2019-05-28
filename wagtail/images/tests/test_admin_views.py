import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import filesizeformat
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import RFC3986_SUBDELIMS, urlquote

from wagtail.core.models import Collection, GroupCollectionPermission
from wagtail.images.views.serve import generate_signature
from wagtail.tests.utils import WagtailTestUtils

from .utils import Image, get_test_image_file

# Get the chars that Django considers safe to leave unescaped in a URL
urlquote_safechars = RFC3986_SUBDELIMS + str('/~:@')


class TestImageIndexView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:index'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/index.html')
        self.assertContains(response, "Add an image")

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_pagination_preserves_other_params(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        for i in range(1, 50):
            self.image = Image.objects.create(
                title="Test image %i" % i,
                file=get_test_image_file(),
                collection=evil_plans_collection
            )

        response = self.get({'collection_id': evil_plans_collection.id, 'p': 2})
        self.assertEqual(response.status_code, 200)

        response_body = response.content.decode('utf8')

        # prev link should exist and include collection_id
        self.assertTrue(
            ("?p=1&amp;collection_id=%i" % evil_plans_collection.id) in response_body
            or ("?collection_id=%i&amp;p=1" % evil_plans_collection.id) in response_body
        )
        # next link should exist and include collection_id
        self.assertTrue(
            ("?p=3&amp;collection_id=%i" % evil_plans_collection.id) in response_body
            or ("?collection_id=%i&amp;p=3" % evil_plans_collection.id) in response_body
        )

    def test_ordering(self):
        orderings = ['title', '-created_at']
        for ordering in orderings:
            response = self.get({'ordering': ordering})
            self.assertEqual(response.status_code, 200)

    def test_collection_order(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")
        root_collection.add_child(name="Good plans")

        response = self.get()
        self.assertEqual(
            [collection.name for collection in response.context['collections']],
            ['Root', 'Evil plans', 'Good plans'])


class TestImageAddView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages:add'), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # as standard, only the root collection exists and so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_get_with_collections(self):
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(name="Evil plans")

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        self.assertContains(response, '<label for="id_collection">')
        self.assertContains(response, "Evil plans")

    def test_add(self):
        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that size was populated correctly
        image = images.first()
        self.assertEqual(image.width, 640)
        self.assertEqual(image.height, 480)

        # Test that the file_size/hash fields were set
        self.assertTrue(image.file_size)
        self.assertTrue(image.file_hash)

        # Test that it was placed in the root collection
        root_collection = Collection.get_first_root_node()
        self.assertEqual(image.collection, root_collection)

    @override_settings(DEFAULT_FILE_STORAGE='wagtail.tests.dummy_external_storage.DummyExternalStorage')
    def test_add_with_external_file_storage(self):
        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        # Check that the image was created
        self.assertTrue(Image.objects.filter(title="Test image").exists())

    def test_add_no_file_selected(self):
        response = self.post({
            'title': "Test image",
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # The form should have an error
        self.assertFormError(response, 'form', 'file', "This field is required.")

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=1)
    def test_add_too_large_file(self):
        file_content = get_test_image_file().file.getvalue()

        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', file_content),
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # The form should have an error
        self.assertFormError(
            response, 'form', 'file',
            "This file is too big ({file_size}). Maximum filesize {max_file_size}.".format(
                file_size=filesizeformat(len(file_content)),
                max_file_size=filesizeformat(1),
            )
        )

    @override_settings(WAGTAILIMAGES_MAX_IMAGE_PIXELS=1)
    def test_add_too_many_pixels(self):
        file_content = get_test_image_file().file.getvalue()

        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', file_content),
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # The form should have an error
        self.assertFormError(
            response, 'form', 'file',
            'This file has too many pixels (307200). Maximum pixels 1.'
        )

    def test_add_with_collections(self):
        root_collection = Collection.get_first_root_node()
        evil_plans_collection = root_collection.add_child(name="Evil plans")

        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
            'collection': evil_plans_collection.id,
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Test that it was placed in the Evil Plans collection
        image = images.first()
        self.assertEqual(image.collection, evil_plans_collection)


class TestImageAddViewWithLimitedCollectionPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        add_image_permission = Permission.objects.get(
            content_type__app_label='wagtailimages', codename='add_image'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_image_permission
        )

        user = get_user_model().objects.create_user(
            username='moriarty',
            email='moriarty@example.com',
            password='password'
        )
        user.groups.add(conspirators_group)

        self.client.login(username='moriarty', password='password')

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:add'), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages:add'), post_data)

    def test_get(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/add.html')

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

    def test_add(self):
        response = self.post({
            'title': "Test image",
            'file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # User should be redirected back to the index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        # Image should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(Image.objects.filter(title="Test image").exists())
        self.assertEqual(
            Image.objects.get(title="Test image").collection,
            self.evil_plans_collection
        )


class TestImageEditView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        self.storage = self.image.file.storage

    def update_from_db(self):
        self.image = Image.objects.get(pk=self.image.pk)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:edit', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages:edit', args=(self.image.id,)), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')

        # Ensure the form supports file uploads
        self.assertContains(response, 'enctype="multipart/form-data"')

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_with_usage_count(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')
        self.assertContains(response, "Used 0 times")
        expected_url = '/admin/images/usage/%d/' % self.image.id
        self.assertContains(response, expected_url)

    @override_settings(DEFAULT_FILE_STORAGE='wagtail.tests.dummy_external_storage.DummyExternalStorage')
    def test_simple_with_external_storage(self):
        # The view calls get_file_size on the image that closes the file if
        # file_size wasn't prevously populated.

        # The view then attempts to reopen the file when rendering the template
        # which caused crashes when certian storage backends were in use.
        # See #1397

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')

    def test_edit(self):
        response = self.post({
            'title': "Edited",
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        self.update_from_db()
        self.assertEqual(self.image.title, "Edited")

    def test_edit_with_new_image_file(self):
        file_content = get_test_image_file().file.getvalue()

        # Change the file size/hash of the image
        self.image.file_size = 100000
        self.image.file_hash = 'abcedf'
        self.image.save()

        response = self.post({
            'title': "Edited",
            'file': SimpleUploadedFile('new.png', file_content),
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        self.update_from_db()
        self.assertNotEqual(self.image.file_size, 100000)
        self.assertNotEqual(self.image.file_hash, 'abcedf')

    @override_settings(DEFAULT_FILE_STORAGE='wagtail.tests.dummy_external_storage.DummyExternalStorage')
    def test_edit_with_new_image_file_and_external_storage(self):
        file_content = get_test_image_file().file.getvalue()

        # Change the file size/hash of the image
        self.image.file_size = 100000
        self.image.file_hash = 'abcedf'
        self.image.save()

        response = self.post({
            'title': "Edited",
            'file': SimpleUploadedFile('new.png', file_content),
        })

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        self.update_from_db()
        self.assertNotEqual(self.image.file_size, 100000)
        self.assertNotEqual(self.image.file_hash, 'abcedf')

    def test_with_missing_image_file(self):
        self.image.file.delete(False)

        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')

    def check_get_missing_file_displays_warning(self):
        # Need to recreate image to use a custom storage per test.
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        image.file.storage.delete(image.file.name)

        response = self.client.get(reverse('wagtailimages:edit', args=(image.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')
        self.assertContains(response, "File not found")

    def test_get_missing_file_displays_warning_with_default_storage(self):
        self.check_get_missing_file_displays_warning()

    @override_settings(DEFAULT_FILE_STORAGE='wagtail.tests.dummy_external_storage.DummyExternalStorage')
    def test_get_missing_file_displays_warning_with_custom_storage(self):
        self.check_get_missing_file_displays_warning()


    def get_content(self, f=None):
        if f is None:
            f = self.image.file
        try:
            if f.closed:
                f.open('rb')
            return f.read()
        finally:
            f.close()

    def test_reupload_same_name(self):
        """
        Checks that reuploading the image file with the same file name
        changes the file name, to avoid browser cache issues (see #3817).
        """
        old_file = self.image.file
        old_size = self.image.file_size
        old_data = self.get_content()

        old_rendition = self.image.get_rendition('fill-5x5')
        old_rendition_data = self.get_content(old_rendition.file)

        new_name = self.image.filename
        new_file = SimpleUploadedFile(
            new_name, get_test_image_file(colour='red').file.getvalue())
        new_size = new_file.size

        response = self.post({
            'title': self.image.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtailimages:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.image.file.name))
        self.assertNotEqual(self.image.file.name,
                            'original_images/' + new_name)
        self.assertNotEqual(self.image.file_size, old_size)
        self.assertEqual(self.image.file_size, new_size)
        self.assertNotEqual(self.get_content(), old_data)

        new_rendition = self.image.get_rendition('fill-5x5')
        self.assertNotEqual(old_rendition.file.name, new_rendition.file.name)
        self.assertNotEqual(self.get_content(new_rendition.file),
                            old_rendition_data)

    def test_reupload_different_name(self):
        """
        Checks that reuploading the image file with a different file name
        correctly uses the new file name.
        """
        old_file = self.image.file
        old_size = self.image.file_size
        old_data = self.get_content()

        old_rendition = self.image.get_rendition('fill-5x5')
        old_rendition_data = self.get_content(old_rendition.file)

        new_name = 'test_reupload_different_name.png'
        new_file = SimpleUploadedFile(
            new_name, get_test_image_file(colour='red').file.getvalue())
        new_size = new_file.size

        response = self.post({
            'title': self.image.title, 'file': new_file,
        })
        self.assertRedirects(response, reverse('wagtailimages:index'))
        self.update_from_db()
        self.assertFalse(self.storage.exists(old_file.name))
        self.assertTrue(self.storage.exists(self.image.file.name))
        self.assertEqual(self.image.file.name,
                         'original_images/' + new_name)
        self.assertNotEqual(self.image.file_size, old_size)
        self.assertEqual(self.image.file_size, new_size)
        self.assertNotEqual(self.get_content(), old_data)

        new_rendition = self.image.get_rendition('fill-5x5')
        self.assertNotEqual(old_rendition.file.name, new_rendition.file.name)
        self.assertNotEqual(self.get_content(new_rendition.file),
                            old_rendition_data)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_no_thousand_separators_in_focal_point_editor(self):
        large_image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(size=(1024, 768)),
        )
        response = self.client.get(reverse('wagtailimages:edit', args=(large_image.id,)))
        self.assertContains(response, 'data-original-width="1024"')


class TestImageDeleteView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:delete', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages:delete', args=(self.image.id,)), post_data)

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=False)
    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/confirm_delete.html')
        self.assertNotIn('Used ', str(response.content))

    @override_settings(WAGTAIL_USAGE_COUNT_ENABLED=True)
    def test_usage_link(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/confirm_delete.html')
        self.assertContains(response, 'Used 0 times')
        expected_url = '/admin/images/usage/%d/' % self.image.id
        self.assertContains(response, expected_url)

    def test_delete(self):
        response = self.post()

        # Should redirect back to index
        self.assertRedirects(response, reverse('wagtailimages:index'))

        # Check that the image was deleted
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 0)


class TestImageChooserView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:chooser'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chooser')
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)

    def test_filter_by_tag(self):
        for i in range(0, 10):
            image = Image.objects.create(
                title="Test image %d is even better than the last one" % i,
                file=get_test_image_file(),
            )
            if i % 2 == 0:
                image.tags.add('even')

        response = self.get({'tag': "even"})
        self.assertEqual(response.status_code, 200)

        # Results should include images tagged 'even'
        self.assertContains(response, "Test image 2 is even better")

        # Results should not include images that just have 'even' in the title
        self.assertNotContains(response, "Test image 3 is even better")

    def test_construct_queryset_hook_browse(self):
        image = Image.objects.create(
            title="Test image shown",
            file=get_test_image_file(),
            uploaded_by_user=self.user,
        )
        Image.objects.create(
            title="Test image not shown",
            file=get_test_image_file(),
        )

        def filter_images(images, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return images.filter(uploaded_by_user=self.user)

        with self.register_hook('construct_image_chooser_queryset', filter_images):
            response = self.get()
        self.assertEqual(len(response.context['images']), 1)
        self.assertEqual(response.context['images'][0], image)

    def test_construct_queryset_hook_search(self):
        image = Image.objects.create(
            title="Test image shown",
            file=get_test_image_file(),
            uploaded_by_user=self.user,
        )
        Image.objects.create(
            title="Test image not shown",
            file=get_test_image_file(),
        )

        def filter_images(images, request):
            # Filter on `uploaded_by_user` because it is
            # the only default FilterField in search_fields
            return images.filter(uploaded_by_user=self.user)

        with self.register_hook('construct_image_chooser_queryset', filter_images):
            response = self.get({'q': 'Test'})
        self.assertEqual(len(response.context['images']), 1)
        self.assertEqual(response.context['images'][0], image)


class TestImageChooserChosenView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:image_chosen', args=(self.image.id,)), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'image_chosen')


class TestImageChooserSelectFormatView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:chooser_select_format', args=(self.image.id,)), params)

    def post(self, post_data={}):
        return self.client.post(reverse('wagtailimages:chooser_select_format', args=(self.image.id,)), post_data)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'select_format')
        self.assertTemplateUsed(response, 'wagtailimages/chooser/select_format.html')

    def test_with_edit_params(self):
        response = self.get(params={'alt_text': "some previous alt text"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value=\\"some previous alt text\\"')

    def test_post_response(self):
        response = self.post({'image-chooser-insertion-format': 'left', 'image-chooser-insertion-alt_text': 'Arthur "two sheds" Jackson'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'image_chosen')
        result = response_json['result']

        self.assertEqual(result['id'], self.image.id)
        self.assertEqual(result['title'], "Test image")
        self.assertEqual(result['format'], 'left')
        self.assertEqual(result['alt'], 'Arthur "two sheds" Jackson')
        self.assertIn('alt="Arthur &quot;two sheds&quot; Jackson"', result['html'])


class TestImageChooserUploadView(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages:chooser_upload'), params)

    def test_simple(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['step'], 'chooser')

    def test_upload(self):
        response = self.client.post(reverse('wagtailimages:chooser_upload'), {
            'image-chooser-upload-title': "Test image",
            'image-chooser-upload-file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
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

        # Test that the file_size/hash fields were set
        self.assertTrue(image.file_size)
        self.assertTrue(image.file_hash)

    def test_upload_no_file_selected(self):
        response = self.client.post(reverse('wagtailimages:chooser_upload'), {
            'image-chooser-upload-title': "Test image",
        })

        # Shouldn't redirect anywhere
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

        # The form should have an error
        self.assertFormError(response, 'uploadform', 'file', "This field is required.")

    def test_pagination_after_upload_form_error(self):
        for i in range(0, 20):
            Image.objects.create(
                title="Test image %d" % i,
                file=get_test_image_file(),
            )

        response = self.client.post(reverse('wagtailimages:chooser_upload'), {
            'image-chooser-upload-title': "Test image",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

        # The re-rendered image chooser listing should be paginated
        self.assertContains(response, "Page 1 of ")
        self.assertEqual(12, len(response.context['images']))

    def test_select_format_flag_after_upload_form_error(self):
        submit_url = reverse('wagtailimages:chooser_upload') + '?select_format=true'
        response = self.client.post(submit_url, {
            'image-chooser-upload-title': "Test image",
            'image-chooser-upload-file': SimpleUploadedFile('not_an_image.txt', b'this is not an image'),
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')
        self.assertFormError(response, 'uploadform', 'file', "Not a supported image format. Supported formats: GIF, JPEG, PNG.")

        # the action URL of the re-rendered form should include the select_format=true parameter
        # (NB the HTML in the response is embedded in a JS string, so need to escape accordingly)
        expected_action_attr = 'action=\\"%s\\"' % submit_url
        self.assertContains(response, expected_action_attr)

    @override_settings(DEFAULT_FILE_STORAGE='wagtail.tests.dummy_external_storage.DummyExternalStorage')
    def test_upload_with_external_storage(self):
        response = self.client.post(reverse('wagtailimages:chooser_upload'), {
            'image-chooser-upload-title': "Test image",
            'image-chooser-upload-file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        # Check response
        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        self.assertTrue(Image.objects.filter(title="Test image").exists())


class TestImageChooserUploadViewWithLimitedPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        add_image_permission = Permission.objects.get(
            content_type__app_label='wagtailimages', codename='add_image'
        )
        admin_permission = Permission.objects.get(
            content_type__app_label='wagtailadmin', codename='access_admin'
        )

        root_collection = Collection.get_first_root_node()
        self.evil_plans_collection = root_collection.add_child(name="Evil plans")

        conspirators_group = Group.objects.create(name="Evil conspirators")
        conspirators_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=conspirators_group,
            collection=self.evil_plans_collection,
            permission=add_image_permission
        )

        user = get_user_model().objects.create_user(
            username='moriarty',
            email='moriarty@example.com',
            password='password'
        )
        user.groups.add(conspirators_group)

        self.client.login(username='moriarty', password='password')

    def test_get(self):
        response = self.client.get(reverse('wagtailimages:chooser_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

    def test_get_chooser(self):
        response = self.client.get(reverse('wagtailimages:chooser'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/chooser/chooser.html')

        # user only has access to one collection, so no 'Collection' option
        # is displayed on the form
        self.assertNotContains(response, '<label for="id_collection">')

    def test_add(self):
        response = self.client.post(reverse('wagtailimages:chooser_upload'), {
            'image-chooser-upload-title': "Test image",
            'image-chooser-upload-file': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        })

        self.assertEqual(response.status_code, 200)

        # Check that the image was created
        images = Image.objects.filter(title="Test image")
        self.assertEqual(images.count(), 1)

        # Image should be created in the 'evil plans' collection,
        # despite there being no collection field in the form, because that's the
        # only one the user has access to
        self.assertTrue(Image.objects.filter(title="Test image").exists())
        self.assertEqual(
            Image.objects.get(title="Test image").collection,
            self.evil_plans_collection
        )


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
        response = self.client.get(reverse('wagtailimages:add_multiple'))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/multiple/add.html')

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=1000)
    def test_add_max_file_size_context_variables(self):
        response = self.client.get(reverse('wagtailimages:add_multiple'))

        self.assertEqual(response.context['max_filesize'], 1000)
        self.assertEqual(
            response.context['error_max_file_size'], "This file is too big. Maximum filesize 1000\xa0bytes."
        )

    def test_add_post(self):
        """
        This tests that a POST request to the add view saves the image and returns an edit form
        """
        response = self.client.post(reverse('wagtailimages:add_multiple'), {
            'files[]': SimpleUploadedFile('test.png', get_test_image_file().file.getvalue()),
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertTemplateUsed(response, 'wagtailimages/multiple/edit_form.html')

        # Check image
        self.assertIn('image', response.context)
        self.assertEqual(response.context['image'].title, 'test.png')
        self.assertTrue(response.context['image'].file_size)
        self.assertTrue(response.context['image'].file_hash)

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
        response = self.client.post(reverse('wagtailimages:add_multiple'), {})

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_nofile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse('wagtailimages:add_multiple'), {}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response
        self.assertEqual(response.status_code, 400)

    def test_add_post_badfile(self):
        """
        This tests that the add view checks for a file when a user POSTs to it
        """
        response = self.client.post(reverse('wagtailimages:add_multiple'), {
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
        self.assertEqual(
            response_json['error_message'], "Not a supported image format. Supported formats: GIF, JPEG, PNG."
        )

    def test_edit_get(self):
        """
        This tests that a GET request to the edit view returns a 405 "METHOD NOT ALLOWED" response
        """
        # Send request
        response = self.client.get(reverse('wagtailimages:edit_multiple', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_edit_post(self):
        """
        This tests that a POST request to the edit view edits the image
        """
        # Send request
        response = self.client.post(reverse('wagtailimages:edit_multiple', args=(self.image.id, )), {
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
        response = self.client.post(reverse('wagtailimages:edit_multiple', args=(self.image.id, )), {
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
        response = self.client.post(reverse('wagtailimages:edit_multiple', args=(self.image.id, )), {
            ('image-%d-title' % self.image.id): "",  # Required
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
        response = self.client.get(reverse('wagtailimages:delete_multiple', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 405)

    def test_delete_post(self):
        """
        This tests that a POST request to the delete view deletes the image
        """
        # Send request
        response = self.client.post(reverse(
            'wagtailimages:delete_multiple', args=(self.image.id, )
        ), HTTP_X_REQUESTED_WITH='XMLHttpRequest')

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

    def test_delete_post_noajax(self):
        """
        This tests that a POST request to the delete view without AJAX returns a 400 response
        """
        # Send request
        response = self.client.post(reverse('wagtailimages:delete_multiple', args=(self.image.id, )))

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
        response = self.client.get(reverse('wagtailimages:url_generator', args=(self.image.id, )))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/url_generator.html')

    def test_get_bad_permissions(self):
        """
        This tests that the view returns a "permission denied" redirect if a user without correct
        permissions attemts to access it
        """
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        # Get
        response = self.client.get(reverse('wagtailimages:url_generator', args=(self.image.id, )))

        # Check response
        self.assertRedirects(response, reverse('wagtailadmin_home'))


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
        response = self.client.get(reverse('wagtailimages:generate_url', args=(self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Check JSON
        content_json = json.loads(response.content.decode())

        self.assertEqual(set(content_json.keys()), set(['url', 'preview_url']))

        expected_url = 'http://localhost/images/%(signature)s/%(image_id)d/fill-800x600/' % {
            'signature': urlquote(generate_signature(self.image.id, 'fill-800x600'), safe=urlquote_safechars),
            'image_id': self.image.id,
        }
        self.assertEqual(content_json['url'], expected_url)

        expected_preview_url = reverse('wagtailimages:preview', args=(self.image.id, 'fill-800x600'))
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
        response = self.client.get(reverse('wagtailimages:generate_url', args=(self.image.id, 'fill-800x600')))

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
        response = self.client.get(reverse('wagtailimages:generate_url', args=(self.image.id + 1, 'fill-800x600')))

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
        response = self.client.get(reverse('wagtailimages:generate_url', args=(self.image.id, 'bad-filter-spec')))

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
        response = self.client.get(reverse('wagtailimages:preview', args=(self.image.id, 'fill-800x600')))

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_get_invalid_filter_spec(self):
        """
        Test that an invalid filter spec returns a 400 response

        This is very unlikely to happen in reality. A user would have
        to create signature for the invalid filter spec which can't be
        done with Wagtails built in URL generator. We should test it
        anyway though.
        """
        # Get the image
        response = self.client.get(reverse('wagtailimages:preview', args=(self.image.id, 'bad-filter-spec')))

        # Check response
        self.assertEqual(response.status_code, 400)


class TestEditOnlyPermissions(TestCase, WagtailTestUtils):
    def setUp(self):
        # Create an image to edit
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )

        # Create a user with change_image permission but not add_image
        user = get_user_model().objects.create_user(
            username='changeonly', email='changeonly@example.com', password='password'
        )
        change_permission = Permission.objects.get(content_type__app_label='wagtailimages', codename='change_image')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')

        image_changers_group = Group.objects.create(name='Image changers')
        image_changers_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(
            group=image_changers_group,
            collection=Collection.get_first_root_node(),
            permission=change_permission
        )

        user.groups.add(image_changers_group)
        self.assertTrue(self.client.login(username='changeonly', password='password'))

    def test_get_index(self):
        response = self.client.get(reverse('wagtailimages:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/index.html')

        # user should not get an "Add an image" button
        self.assertNotContains(response, "Add an image")

        # user should be able to see images not owned by them
        self.assertContains(response, "Test image")

    def test_search(self):
        response = self.client.get(reverse('wagtailimages:index'), {'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_get_add(self):
        response = self.client.get(reverse('wagtailimages:add'))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))

    def test_get_edit(self):
        response = self.client.get(reverse('wagtailimages:edit', args=(self.image.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/edit.html')

    def test_get_delete(self):
        response = self.client.get(reverse('wagtailimages:delete', args=(self.image.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/images/confirm_delete.html')

    def test_get_add_multiple(self):
        response = self.client.get(reverse('wagtailimages:add_multiple'))
        # permission should be denied
        self.assertRedirects(response, reverse('wagtailadmin_home'))


class TestImageAddMultipleView(TestCase, WagtailTestUtils):
    def test_as_superuser(self):
        self.login()
        response = self.client.get(reverse('wagtailimages:add_multiple'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/multiple/add.html')

    def test_as_ordinary_editor(self):
        user = get_user_model().objects.create_user(username='editor', email='editor@email.com', password='password')

        add_permission = Permission.objects.get(content_type__app_label='wagtailimages', codename='add_image')
        admin_permission = Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        image_adders_group = Group.objects.create(name='Image adders')
        image_adders_group.permissions.add(admin_permission)
        GroupCollectionPermission.objects.create(group=image_adders_group, collection=Collection.get_first_root_node(), permission=add_permission)
        user.groups.add(image_adders_group)

        self.client.login(username='editor', password='password')

        response = self.client.get(reverse('wagtailimages:add_multiple'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/multiple/add.html')
