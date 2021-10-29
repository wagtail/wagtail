from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.utils import WagtailTestUtils


Image = get_image_model()
test_file = get_test_image_file()


def get_tag_list(image):
    return [tag.name for tag in image.tags.all()]


class TestBulkAddTags(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.new_tags = ['first', 'second']
        self.images = [
            Image.objects.create(title=f"Test image - {i}", file=test_file) for i in range(1, 6)
        ]
        self.url = reverse('wagtail_bulk_action', args=('wagtailimages', 'image', 'add_tags',)) + '?'
        for image in self.images:
            self.url += f'id={image.id}&'
        self.post_data = {'tags': ','.join(self.new_tags)}

    def test_add_tags_with_limited_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(content_type__app_label='wagtailadmin', codename='access_admin')
        )
        self.user.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        self.assertInHTML("<p>You don't have permission to add tags to these images</p>", html)

        for image in self.images:
            self.assertInHTML('<li>{image_title}</li>'.format(image_title=image.title), html)

        response = self.client.post(self.url, self.post_data)

        # New tags should not be added to the images
        for image in self.images:
            self.assertCountEqual(get_tag_list(Image.objects.get(id=image.id)), [])

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtailimages/bulk_actions/confirm_bulk_add_tags.html')

    def test_add_tags(self):
        # Make post request
        response = self.client.post(self.url, self.post_data)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # New tags should not be added to the images
        for image in self.images:
            self.assertCountEqual(get_tag_list(Image.objects.get(id=image.id)), self.new_tags)
