from django.test import TestCase
from django.test.client import Client
from wagtail.wagtailembeds import get_embed


class TestEmbeds(TestCase):
    def setUp(self):
        self.hit_count = 0

    def test_get_embed_title(self):
        self.assertEqual(self.dummy_embed().title, "Test: www.test.com/1234",
                         "Check that the embed title is correct")

    def test_get_embed_type(self):
        self.assertEqual(self.dummy_embed().type, "video", "Check that the embed type is correct")

    def test_get_embed_width(self):
        self.assertEqual(self.dummy_embed().width, 400, "Check that the embed type is correct")

    def test_get_embed_hit_count_hit(self):
        self.dummy_embed()
        self.assertEqual(self.hit_count, 1, "Check that there has only been one hit to the backend")

    def test_get_embed_hit_count_stasis(self):
        self.dummy_embed()
        self.dummy_embed()
        self.assertEqual(self.hit_count, 1,
                         "Look for the same embed again and check the hit count hasn't increased")

    def test_get_multiple_embed_hit_count_change(self):
        self.dummy_embed()
        self.dummy_embed(4321)
        self.assertEqual(self.hit_count, 2, "Look for a different embed, hit count should increase")

    def test_get_embed_width_hit_count_change(self):
        self.dummy_embed(4321)
        self.dummy_embed(4321, None)
        self.assertEqual(self.hit_count, 2,
                         "Look for the same embed with a different width, this should also increase hit count")

    def dummy_embed(self, num=1234, max_width=400):
        return get_embed('www.test.com/%d' % num, max_width=max_width, finder=self.dummy_finder)

    def dummy_finder(self, url, max_width=None):
        # Up hit count
        self.hit_count += 1

        # Return a pretend record
        return {
            'title': "Test: " + url,
            'type': 'video',
            'thumbnail_url': '',
            'width': max_width if max_width else 640,
            'height': 480,
            'html': "<p>Blah blah blah</p>",
        }


def get_default_host():
    from wagtail.wagtailcore.models import Site
    return Site.objects.filter(is_default_site=True).first().root_url.split('://')[1]


class TestChooser(TestCase):
    def setUp(self):
        # Create a user
        from django.contrib.auth.models import User
        User.objects.create_superuser(username='test', email='test@email.com', password='password')

        # Setup client
        self.c = Client()
        login = self.c.login(username='test', password='password')
        self.assertEqual(login, True)

    def test_chooser(self):
        r = self.c.get('/admin/embeds/chooser/', HTTP_HOST=get_default_host())
        self.assertEqual(r.status_code, 200)

        # TODO: Test submitting
