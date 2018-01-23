from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings

from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url
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
