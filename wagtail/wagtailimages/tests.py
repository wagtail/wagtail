from django.test import TestCase
from django.contrib.auth.models import User, Group, Permission
from wagtail.wagtailcore.models import Site
from wagtail.wagtailimages.models import get_image_model
from django.core.urlresolvers import reverse


Image = get_image_model()


class TestImage(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            width=640,
            height=480,
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

        # Owner user must have the add_document permission
        self.owner.user_permissions.add(Permission.objects.get(codename='add_image'))

        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image",
            uploaded_by_user=self.owner,
            width=640,
            height=480,
        )

    def test_administrator_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.administrator))

    def test_editor_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.editor))

    def test_owner_can_edit(self):
        self.assertTrue(self.image.is_editable_by_user(self.owner))

    def test_user_cant_edit(self):
        self.assertFalse(self.image.is_editable_by_user(self.user))


## ===== ADMIN VIEWS =====

def get_default_host():
    return Site.objects.filter(is_default_site=True).first().root_url.split('://')[1]


def login(client):
    # Create a user
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')


class TestImageIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_index'), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['search_query'], "Hello")

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
        return self.client.get(reverse('wagtailimages_add_image'), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestImageChooserView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser'), params, HTTP_HOST=get_default_host())

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


class TestImageChooserUploadView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get(reverse('wagtailimages_chooser_upload'), params, HTTP_HOST=get_default_host())

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
