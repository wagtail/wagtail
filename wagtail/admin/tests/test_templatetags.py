from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url, notification_static
from wagtail.images.tests.utils import get_test_image_file
from wagtail.users.models import UserProfile


class TestAvatarTemplateTag(TestCase):
    def setUp(self):
        # Create a user
        self.test_user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@email.com',
            password='password',
        )

    def test_use_gravatar_by_default(self):
        url = avatar_url(self.test_user)
        self.assertIn('www.gravatar.com', url)

    def test_skip_gravatar_if_no_email(self):
        self.test_user.email = ''
        url = avatar_url(self.test_user)
        self.assertIn('default-user-avatar', url)

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL='https://robohash.org')
    def test_custom_gravatar_provider(self):
        url = avatar_url(self.test_user)
        self.assertIn('robohash.org', url)

    @override_settings(WAGTAIL_GRAVATAR_PROVIDER_URL=None)
    def test_disable_gravatar(self):
        url = avatar_url(self.test_user)
        self.assertIn('default-user-avatar', url)

    def test_uploaded_avatar(self):
        user_profile = UserProfile.get_for_user(self.test_user)
        user_profile.avatar = get_test_image_file(filename='custom-avatar.png')
        user_profile.save()

        url = avatar_url(self.test_user)
        self.assertIn('custom-avatar', url)


class TestNotificationStaticTemplateTag(TestCase):
    @override_settings(STATIC_URL='/static/')
    def test_local_notification_static(self):
        url = notification_static('wagtailadmin/images/email-header.jpg')
        self.assertEqual('/static/wagtailadmin/images/email-header.jpg', url)

    @override_settings(STATIC_URL='/static/', BASE_URL='http://localhost:8000')
    def test_local_notification_static_baseurl(self):
        url = notification_static('wagtailadmin/images/email-header.jpg')
        self.assertEqual('http://localhost:8000/static/wagtailadmin/images/email-header.jpg', url)

    @override_settings(STATIC_URL='https://s3.amazonaws.com/somebucket/static/', BASE_URL='http://localhost:8000')
    def test_remote_notification_static(self):
        url = notification_static('wagtailadmin/images/email-header.jpg')
        self.assertEqual('https://s3.amazonaws.com/somebucket/static/wagtailadmin/images/email-header.jpg', url)


class TestVersionedStatic(TestCase):
    def test_versioned_static(self):
        result = versioned_static('wagtailadmin/js/core.js')
        self.assertRegex(result, r'^/static/wagtailadmin/js/core.js\?v=(\w+)$')

    @mock.patch('wagtail.admin.staticfiles.static')
    def test_versioned_static_version_string(self, mock_static):
        mock_static.return_value = '/static/wagtailadmin/js/core.js?v=123'
        result = versioned_static('wagtailadmin/js/core.js')
        self.assertEqual(result, '/static/wagtailadmin/js/core.js?v=123')
        mock_static.assert_called_once_with('wagtailadmin/js/core.js')

    def test_versioned_static_absolute_path(self):
        result = versioned_static('/static/wagtailadmin/js/core.js')
        self.assertEqual(result, '/static/wagtailadmin/js/core.js')

    def test_versioned_static_url(self):
        result = versioned_static('http://example.org/static/wagtailadmin/js/core.js')
        self.assertEqual(result, 'http://example.org/static/wagtailadmin/js/core.js')
