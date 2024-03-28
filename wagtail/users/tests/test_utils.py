from django.test import TestCase
from wagtail.users.utils import get_gravatar_url

class TestGravatar(TestCase):
    def test_gravatar_default(self):
        # Test with the default settings
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=100",
        )

    def test_gravatar_custom_size(self):
        # Test with a custom size (note that the size will be doubled)
        self.assertEqual(
            get_gravatar_url("something@example.com", size=100),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?d=mp&s=200",
        )
