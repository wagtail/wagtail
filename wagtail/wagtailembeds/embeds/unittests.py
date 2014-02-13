import unittest
import oembed

# Test that a bunch of oembed examples is working
# If any of these is removed or changed then the unit test will fail
# This is a unittest TestCase (and not a django.test one) since django 
# database is not actually needed for these tests

TEST_DATA = [
    {
        'url':'http://www.youtube.com/watch?v=S3xAeTmsJfg',
        'title':'Animation: Ferret dance (A series of tubes)'
    },
    {
        'url':'http://vimeo.com/86036070',
        'title':'Wagtail: A new Django CMS'
    },
    {
        'url':'https://speakerdeck.com/harmstyler/an-introduction-to-django',
        'title':'An Introduction to Django'
    },
    {
        'url':'https://ifttt.com/recipes/144705-new-twitter-followers-in-a-google-spreadsheet',
        'title':'New Twitter followers in a Google spreadsheet'
    },
    {
        'url':'http://www.hulu.com/watch/20807/late-night-with-conan-obrien-wed-may-21-2008',
        'title':'Wed, May 21, 2008 (Late Night With Conan O\'Brien)'
    },
    {
        'url':'http://www.flickr.com/photos/dfluke/5995957175/',
        'title':'Django pony!?'
    },
    {
        'url':'http://www.slideshare.net/simon/the-django-web-application-framework',
        'title':'The Django Web Application Framework'
    },
    {
        'url':'http://www.rdio.com/artist/The_Black_Keys/album/Brothers/',
        'title':'Brothers'
    },
    {
        'url':'http://instagram.com/p/kFKCcEKmBq/',
        'title':'Family holidays in #Greece!'
    },
    {
        'url':'https://www.kickstarter.com/projects/noujaimfilms/the-square-a-film-about-the-egyptian-revolution',
        'title':'Sundance Award Winning Film on the Egyptian Revolution'
    },
    {
        'url':'http://www.dailymotion.com/video/xoxulz_babysitter_animals',
        'title':'Babysitter!'
    }
]

class TestEmbeds(unittest.TestCase):
    def test_get_embed_oembed(self):
        for td in TEST_DATA:
            embed = oembed.get_embed_oembed_low(td['url'])
            self.assertEqual(embed['title'], td['title'] )
            self.assertIsNotNone(embed['type'] )
            self.assertIsNotNone(embed['width'] )
            self.assertIsNotNone(embed['height'] )

if __name__ == '__main__':
    unittest.main()        