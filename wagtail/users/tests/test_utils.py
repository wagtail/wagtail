from django.test import TestCase

from wagtail.users.utils import get_gravatar_url


class TestGravatar(TestCase):
    def test_gravatar(self):
        self.assertEqual(
            get_gravatar_url("something@example.com"),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a?s=100&d=mp",
        )
        self.assertEqual(
            get_gravatar_url("something@example.com", default="robohash"),
            "//www.gravatar.com/avatar/76ebd6fecabc982c205dd056e8f0415a"
            "?s=100&d=robohash",
        )
