from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.tests.utils import WagtailTestUtils


Document = get_document_model()


def get_tag_list(document):
    return [tag.name for tag in document.tags.all()]


class TestBulkAddTags(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.login()
        self.new_tags = ['first', 'second']
        self.documents = [
            Document.objects.create(title=f"Test document - {i}") for i in range(1, 6)
        ]
        self.url = reverse('wagtaildocs:document_bulk_action', args=('add_tags',)) + '?'
        for document in self.documents:
            self.url += f'id={document.id}&'
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
        self.assertInHTML("<p>You don't have permission to add tags to these documents</p>", html)

        needle = '<ul>'
        for document in self.documents:
            needle += '<li>{document_title}</li>'.format(document_title=document.title)
        needle += '</ul>'
        self.assertInHTML(needle, html)

        response = self.client.post(self.url, self.post_data)

        # New tags should not be added to the documents
        for document in self.documents:
            self.assertCountEqual(get_tag_list(Document.objects.get(id=document.id)), [])

    def test_simple(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'wagtaildocs/bulk_actions/confirm_bulk_add_tags.html')

    def test_add_tags(self):
        # Make post request
        response = self.client.post(self.url, self.post_data)

        # User should be redirected back to the index
        self.assertEqual(response.status_code, 302)

        # New tags should not be added to the documents
        for document in self.documents:
            self.assertCountEqual(get_tag_list(Document.objects.get(id=document.id)), self.new_tags)
