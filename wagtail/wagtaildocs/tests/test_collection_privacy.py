from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from django.utils.six import b

from wagtail.core.models import Collection, CollectionViewRestriction
from wagtail.wagtaildocs.models import Document

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote


class TestCollectionPrivacyDocument(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.fake_file = ContentFile(b("A boring example document"))
        self.fake_file.name = 'test.txt'
        self.password_collection = Collection.objects.get(name='Password protected')
        self.login_collection = Collection.objects.get(name='Login protected')
        self.group_collection = Collection.objects.get(name='Group protected')
        self.view_restriction = CollectionViewRestriction.objects.get(collection=self.password_collection)
        self.event_editors_group = Group.objects.get(name='Event editors')

    def get_document(self, collection):
        secret_document = Document.objects.create(
            title="Test document",
            file=self.fake_file,
            collection=collection,
        )
        url = reverse('wagtaildocs_serve', args=(secret_document.id, secret_document.filename))
        response = self.client.get(url)
        return response, quote(url)

    def test_anonymous_user_must_authenticate(self):
        secret_document = Document.objects.create(
            title="Test document", file=self.fake_file, collection=self.password_collection
        )
        doc_url = reverse('wagtaildocs_serve', args=(secret_document.id, secret_document.filename))
        response = self.client.get(doc_url)
        self.assertEqual(response.templates[0].name, 'wagtaildocs/password_required.html')

        submit_url = reverse('wagtaildocs_authenticate_with_password', args=[self.view_restriction.id])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="{}" />'.format(doc_url),
            html=True
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(submit_url, {
            'password': 'wrongpassword',
            'return_url': doc_url,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'wagtaildocs/password_required.html')
        self.assertContains(response, '<form action="%s"' % submit_url)

        # posting the correct password should redirect back to return_url
        response = self.client.post(submit_url, {
            'password': 'swordfish',
            'return_url': doc_url,
        })
        self.assertRedirects(response, doc_url)

        # now requests to the documents url should pass authentication
        response = self.client.get(doc_url)

    def test_group_restriction_with_anonymous_user(self):
        response, url = self.get_document(self.group_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_group_restriction_with_unpermitted_user(self):
        self.client.login(username='eventmoderator', password='password')
        response, url = self.get_document(self.group_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_group_restriction_with_permitted_user(self):
        self.client.login(username='eventeditor', password='password')
        response, url = self.get_document(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_group_restriction_with_superuser(self):
        self.client.login(username='superuser', password='password')
        response, url = self.get_document(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_login_restriction_with_anonymous_user(self):
        response, url = self.get_document(self.login_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_login_restriction_with_logged_in_user(self):
        self.client.login(username='eventmoderator', password='password')
        response, url = self.get_document(self.login_collection)
        self.assertEqual(response.status_code, 200)
