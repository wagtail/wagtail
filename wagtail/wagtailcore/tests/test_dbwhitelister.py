from django.test import TestCase
from wagtail.wagtailcore.rich_text import DbWhitelister
from wagtail.wagtailcore.whitelist import Whitelister

from bs4 import BeautifulSoup

class TestDbWhitelister(TestCase):
    def assertHtmlEqual(self, str1, str2):
        """
        Assert that two HTML strings are equal at the DOM level
        (necessary because we can't guarantee the order that attributes are output in)
        """
        self.assertEqual(BeautifulSoup(str1), BeautifulSoup(str2))

    def test_page_link_is_rewritten(self):
        input_html = '<p>Look at the <a data-linktype="page" data-id="2" href="/">lovely homepage</a> of my <a href="http://wagtail.io/">Wagtail</a> site</p>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<p>Look at the <a linktype="page" id="2">lovely homepage</a> of my <a href="http://wagtail.io/">Wagtail</a> site</p>'
        self.assertHtmlEqual(expected, output_html)

    def test_document_link_is_rewritten(self):
        input_html = '<p>Look at our <a data-linktype="document" data-id="1" href="/documents/1/brochure.pdf">horribly oversized brochure</a></p>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<p>Look at our <a linktype="document" id="1">horribly oversized brochure</a></p>'
        self.assertHtmlEqual(expected, output_html)

    def test_image_embed_is_rewritten(self):
        input_html = '<p>OMG look at this picture of a kitten:</p><figure data-embedtype="image" data-id="5" data-format="image-with-caption" data-alt="A cute kitten" class="fancy-image"><img src="/media/images/kitten.jpg" width="320" height="200" alt="A cute kitten" /><figcaption>A kitten, yesterday.</figcaption></figure>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<p>OMG look at this picture of a kitten:</p><embed embedtype="image" id="5" format="image-with-caption" alt="A cute kitten" />'
        self.assertHtmlEqual(expected, output_html)

    def test_media_embed_is_rewritten(self):
        input_html = '<p>OMG look at this video of a kitten: <iframe data-embedtype="media" data-url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" width="640" height="480" src="//www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe></p>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<p>OMG look at this video of a kitten: <embed embedtype="media" url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" /></p>'
        self.assertHtmlEqual(expected, output_html)

    def test_div_conversion(self):
        # DIVs should be converted to P, and all whitelist / conversion rules still applied
        input_html = '<p>before</p><div class="shiny">OMG <b>look</b> at this <blink>video</blink> of a kitten: <iframe data-embedtype="media" data-url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" width="640" height="480" src="//www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe></div><p>after</p>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<p>before</p><p>OMG <b>look</b> at this video of a kitten: <embed embedtype="media" url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" /></p><p>after</p>'
        self.assertHtmlEqual(expected, output_html)

    def test_whitelist_hooks(self):
        # wagtail.tests.wagtail_hooks overrides the whitelist to permit <blockquote> and <a target="...">
        input_html = '<blockquote>I would put a tax on all people who <a href="https://twitter.com/DMReporter/status/432914941201223680/photo/1" target="_blank" tea="darjeeling">stand in water</a>.</blockquote><p>- <character>Gumby</character></p>'
        output_html = DbWhitelister.clean(input_html)
        expected = '<blockquote>I would put a tax on all people who <a href="https://twitter.com/DMReporter/status/432914941201223680/photo/1" target="_blank">stand in water</a>.</blockquote><p>- Gumby</p>'
        self.assertHtmlEqual(expected, output_html)

        # check that the base Whitelister class is unaffected by these custom whitelist rules
        input_html = '<blockquote>I would put a tax on all people who <a href="https://twitter.com/DMReporter/status/432914941201223680/photo/1" target="_blank" tea="darjeeling">stand in water</a>.</blockquote><p>- <character>Gumby</character></p>'
        output_html = Whitelister.clean(input_html)
        expected = 'I would put a tax on all people who <a href="https://twitter.com/DMReporter/status/432914941201223680/photo/1">stand in water</a>.<p>- Gumby</p>'
        self.assertHtmlEqual(expected, output_html)
