from django.test import TestCase
from django.contrib.auth.models import User
from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url

class AvatarUrlTest(TestCase):
    def setUp(self):
        self.user_with_custom_avatar = User.objects.create(username="fred_user")
        self.user_with_default_avatar = User.objects.create(username="jane_user")

    def test_custom_avatar_url(self):
        url = avatar_url(self.user_with_custom_avatar, size=100)
        self.assertEqual(url, "https://example.com/avatars/fred-100.png")

    def test_default_avatar_url(self):
        url = avatar_url(self.user_with_default_avatar, size=100)
        self.assertIn("gravatar.com", url)  # or other default logic
