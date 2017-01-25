from __future__ import absolute_import, unicode_literals
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.six import b

from wagtail.wagtailcore.models import Collection, CollectionViewRestriction
from wagtail.wagtaildocs.models import Document
from wagtail.wagtailimages.views.serve import generate_signature
from wagtail.wagtailimages.tests.utils import Image, get_test_image_file


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
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')

        content_type = ContentType.objects.get_for_model(secret_document)
        submit_url = "/_util/authenticate_with_password/collection/%d/%d/%d/" % (
            self.view_restriction.id, content_type.id, secret_document.id
        )
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="{}" />'.format(doc_url)
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(submit_url, {
            'password': 'wrongpassword',
            'return_url': doc_url,
        })
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')
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


class TestCollectionPrivacyImage(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.password_collection = Collection.objects.get(name='Password protected')
        self.login_collection = Collection.objects.get(name='Login protected')
        self.group_collection = Collection.objects.get(name='Group protected')
        self.view_restriction = CollectionViewRestriction.objects.get(collection=self.password_collection)
        self.event_editors_group = Group.objects.get(name='Event editors')

    def get_image(self, collection):
        image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
            collection=collection,
        )
        # Generate signature
        signature = generate_signature(image.id, 'fill-800x600')
        # Generate url
        url = reverse('wagtailimages_serve', args=(signature, image.id, 'fill-800x600'))
        # Get the image
        response = self.client.get(url)
        return response, quote(url)

    def test_anonymous_user_must_authenticate(self):
        # now an image
        secret_image = Image.objects.create(
            title="Test image",
            file=get_test_image_file(),
            collection=self.password_collection,
        )
        # Generate signature
        signature = generate_signature(secret_image.id, 'fill-800x600')
        # Generate url
        url = reverse('wagtailimages_serve', args=(signature, secret_image.id, 'fill-800x600'))
        response = self.client.get(url)
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')

        content_type = ContentType.objects.get_for_model(secret_image)
        submit_url = "/_util/authenticate_with_password/collection/%d/%d/%d/" % (
            self.view_restriction.id, content_type.id, secret_image.id
        )
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="{}" />'.format(url)
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(submit_url, {
            'password': 'wrongpassword',
            'return_url': url,
        })
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')
        self.assertContains(response, '<form action="%s"' % submit_url)

        # posting the correct password should redirect back to return_url
        response = self.client.post(submit_url, {
            'password': 'swordfish',
            'return_url': url,
        })
        self.assertRedirects(response, url)

        # now requests to the documents url should pass authentication
        response = self.client.get(url)

    def test_group_restriction_with_anonymous_user(self):
        response, url = self.get_image(self.group_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_group_restriction_with_unpermitted_user(self):
        self.client.login(username='eventmoderator', password='password')
        response, url = self.get_image(self.group_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_group_restriction_with_permitted_user(self):
        self.client.login(username='eventeditor', password='password')
        response, url = self.get_image(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_group_restriction_with_superuser(self):
        self.client.login(username='superuser', password='password')
        response, url = self.get_image(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_login_restriction_with_anonymous_user(self):
        response, url = self.get_image(self.login_collection)
        self.assertRedirects(response, '/_util/login/?next={}'.format(url))

    def test_login_restriction_with_logged_in_user(self):
        self.client.login(username='eventmoderator', password='password')
        response, url = self.get_image(self.login_collection)
        self.assertEqual(response.status_code, 200)
