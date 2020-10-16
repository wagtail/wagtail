from functools import partial

from django.test import TestCase
from django.utils.safestring import SafeString

from wagtail.admin import compare
from wagtail.core.blocks import StreamValue
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.tests.testapp.models import (
    AdvertWithCustomPrimaryKey, EventCategory, EventPage, EventPageSpeaker,
    HeadCountRelatedModelUsingPK, SimplePage, SnippetChooserModelWithCustomPrimaryKey, StreamPage,
    TaggedPage)


class TestFieldComparison(TestCase):
    comparison_class = compare.FieldComparison

    def test_hasnt_changed(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="Content"),
            SimplePage(content="Content"),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Content")
        self.assertEqual(comparison.htmldiff(), 'Content')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="Original content"),
            SimplePage(content="Modified content"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original content</span><span class="addition">Modified content</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_htmldiff_escapes_value(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content='Original content'),
            SimplePage(content='<script type="text/javascript">doSomethingBad();</script>'),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original content</span><span class="addition">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)


class TestTextFieldComparison(TestFieldComparison):
    comparison_class = compare.TextFieldComparison

    # Only change from FieldComparison is the HTML diff is performed on words
    # instead of the whole field value.
    def test_has_changed(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="Original content"),
            SimplePage(content="Modified content"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original</span><span class="addition">Modified</span> content')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_from_none_to_value_only_shows_addition(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content=None),
            SimplePage(content="Added content")
        )

        self.assertEqual(comparison.htmldiff(), '<span class="addition">Added content</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_from_value_to_none_only_shows_deletion(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="Removed content"),
            SimplePage(content=None)
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Removed content</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())


class TestRichTextFieldComparison(TestFieldComparison):
    comparison_class = compare.RichTextFieldComparison

    # Only change from FieldComparison is the HTML diff is performed on words
    # instead of the whole field value.
    def test_has_changed(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="Original content"),
            SimplePage(content="Modified content"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original</span><span class="addition">Modified</span> content')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    # Only change from FieldComparison is that this comparison disregards HTML tags
    def test_has_changed_html(self):
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content="<b>Original</b> content"),
            SimplePage(content="Modified <i>content</i>"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original</span><span class="addition">Modified</span> content')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_htmldiff_escapes_value(self):
        # Need to override this one as the HTML tags are stripped by RichTextFieldComparison
        comparison = self.comparison_class(
            SimplePage._meta.get_field('content'),
            SimplePage(content='Original content'),
            SimplePage(content='<script type="text/javascript">doSomethingBad();</script>'),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Original content</span><span class="addition">doSomethingBad();</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)


class TestStreamFieldComparison(TestCase):
    comparison_class = compare.StreamFieldComparison

    def test_hasnt_changed(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
            ])),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Body")
        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Content</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Original content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Modified content", '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object"><span class="deletion">Original</span><span class="addition">Modified</span> content</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_add_block(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
                ('text', "New Content", '2'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Content</div>\n<div class="comparison__child-object addition">New Content</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_delete_block(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
                ('text', "Content Foo", '2'),
                ('text', "Content Bar", '3'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
                ('text', "Content Bar", '3'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Content</div>\n<div class="comparison__child-object deletion">Content Foo</div>\n<div class="comparison__child-object">Content Bar</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_edit_block(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
                ('text', "Content Foo", '2'),
                ('text', "Content Bar", '3'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Content", '1'),
                ('text', "Content Baz", '2'),
                ('text', "Content Bar", '3'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Content</div>\n<div class="comparison__child-object">Content <span class="deletion">Foo</span><span class="addition">Baz</span></div>\n<div class="comparison__child-object">Content Bar</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_has_changed_richtext(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "<b>Original</b> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "Modified <i>content</i>", '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object"><span class="deletion">Original</span><span class="addition">Modified</span> content</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_htmldiff_escapes_value_on_change(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "I <b>really</b> like original<i>ish</i> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', 'I <b>really</b> like evil code <script type="text/javascript">doSomethingBad();</script>', '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">I &lt;b&gt;really&lt;/b&gt; like <span class="deletion">original&lt;i&gt;ish&lt;/i&gt; content</span><span class="addition">evil code &lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</span></div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_escapes_value_on_addition(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Original <em>and unchanged</em> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Original <em>and unchanged</em> content", '1'),
                ('text', '<script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original &lt;em&gt;and unchanged&lt;/em&gt; content</div>\n<div class="comparison__child-object addition">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_escapes_value_on_deletion(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Original <em>and unchanged</em> content", '1'),
                ('text', '<script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('text', "Original <em>and unchanged</em> content", '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original &lt;em&gt;and unchanged&lt;/em&gt; content</div>\n<div class="comparison__child-object deletion">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_richtext_strips_tags_on_change(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "I <b>really</b> like Wagtail &lt;3", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', 'I <b>really</b> like evil code &gt;_&lt; <script type="text/javascript">doSomethingBad();</script>', '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">I really like <span class="deletion">Wagtail &lt;3</span><span class="addition">evil code &gt;_&lt; doSomethingBad();</span></div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_richtext_strips_tags_on_addition(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "Original <em>and unchanged</em> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "Original <em>and unchanged</em> content", '1'),
                ('rich_text', 'I <b>really</b> like evil code &gt;_&lt; <script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original and unchanged content</div>\n<div class="comparison__child-object addition">I really like evil code &gt;_&lt; doSomethingBad();</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_richtext_strips_tags_on_deletion(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "Original <em>and unchanged</em> content", '1'),
                ('rich_text', 'I <b>really</b> like evil code &gt;_&lt; <script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('rich_text', "Original <em>and unchanged</em> content", '1'),
            ])),
        )

        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original and unchanged content</div>\n<div class="comparison__child-object deletion">I really like evil code &gt;_&lt; doSomethingBad();</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_raw_html_escapes_value_on_change(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', "Original<i>ish</i> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', '<script type="text/javascript">doSomethingBad();</script>', '1'),
            ])),
        )
        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object"><span class="deletion">Original&lt;i&gt;ish&lt;/i&gt; content</span><span class="addition">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</span></div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_raw_html_escapes_value_on_addition(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', "Original <em>and unchanged</em> content", '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', "Original <em>and unchanged</em> content", '1'),
                ('raw_html', '<script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
        )
        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original &lt;em&gt;and unchanged&lt;/em&gt; content</div>\n<div class="comparison__child-object addition">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_htmldiff_raw_html_escapes_value_on_deletion(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', "Original <em>and unchanged</em> content", '1'),
                ('raw_html', '<script type="text/javascript">doSomethingBad();</script>', '2'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('raw_html', "Original <em>and unchanged</em> content", '1'),
            ])),
        )
        self.assertEqual(comparison.htmldiff(), '<div class="comparison__child-object">Original &lt;em&gt;and unchanged&lt;/em&gt; content</div>\n<div class="comparison__child-object deletion">&lt;script type=&quot;text/javascript&quot;&gt;doSomethingBad();&lt;/script&gt;</div>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_compare_structblock(self):
        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('product', {'name': 'a packet of rolos', 'price': '75p'}, '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('product', {'name': 'a packet of rolos', 'price': '85p'}, '1'),
            ])),
        )

        expected = """
            <div class="comparison__child-object"><dl>
                <dt>Name</dt>
                <dd>a packet of rolos</dd>
                <dt>Price</dt>
                <dd><span class="deletion">75p</span><span class="addition">85p</span></dd>
            </dl></div>
        """
        self.assertHTMLEqual(comparison.htmldiff(), expected)
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_compare_nested_streamblock_uses_comparison_class(self):
        field = StreamPage._meta.get_field('body')
        stream_block = field.stream_block.child_blocks['books']
        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('books', StreamValue(stream_block, [('title', 'The Old Man and the Sea', '10')]), '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('books', StreamValue(stream_block, [('author', 'Oscar Wilde', '11')]), '1'),
            ])),
        )
        expected = """
            <div class="comparison__child-object">
                <div class="comparison__child-object addition">Oscar Wilde</div>\n
                <div class="comparison__child-object deletion">The Old Man and the Sea</div>
            </div>
        """
        self.assertHTMLEqual(comparison.htmldiff(), expected)
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_compare_imagechooserblock(self):
        image_model = get_image_model()
        test_image_1 = image_model.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )
        test_image_2 = image_model.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )

        field = StreamPage._meta.get_field('body')

        comparison = self.comparison_class(
            field,
            StreamPage(body=StreamValue(field.stream_block, [
                ('image', test_image_1, '1'),
            ])),
            StreamPage(body=StreamValue(field.stream_block, [
                ('image', test_image_2, '1'),
            ])),
        )

        result = comparison.htmldiff()
        self.assertIn('<div class="preview-image deletion">', result)
        self.assertIn('alt="Test image 1"', result)
        self.assertIn('<div class="preview-image addition">', result)
        self.assertIn('alt="Test image 2"', result)

        self.assertIsInstance(result, SafeString)
        self.assertTrue(comparison.has_changed())


class TestChoiceFieldComparison(TestCase):
    comparison_class = compare.ChoiceFieldComparison

    def test_hasnt_changed(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('audience'),
            EventPage(audience="public"),
            EventPage(audience="public"),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Audience")
        self.assertEqual(comparison.htmldiff(), 'Public')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('audience'),
            EventPage(audience="public"),
            EventPage(audience="private"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Public</span><span class="addition">Private</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_from_none_to_value_only_shows_addition(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('audience'),
            EventPage(audience=None),
            EventPage(audience="private"),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="addition">Private</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())

    def test_from_value_to_none_only_shows_deletion(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('audience'),
            EventPage(audience="public"),
            EventPage(audience=None),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Public</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())


class TestTagsFieldComparison(TestCase):
    comparison_class = compare.TagsFieldComparison

    def test_hasnt_changed(self):
        a = TaggedPage()
        a.tags.add('wagtail')
        a.tags.add('bird')

        b = TaggedPage()
        b.tags.add('wagtail')
        b.tags.add('bird')

        comparison = self.comparison_class(TaggedPage._meta.get_field('tags'), a, b)

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Tags")
        self.assertEqual(comparison.htmldiff(), 'wagtail, bird')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        a = TaggedPage()
        a.tags.add('wagtail')
        a.tags.add('bird')

        b = TaggedPage()
        b.tags.add('wagtail')
        b.tags.add('motacilla')

        comparison = self.comparison_class(TaggedPage._meta.get_field('tags'), a, b)

        self.assertEqual(comparison.htmldiff(), 'wagtail, <span class="deletion">bird</span>, <span class="addition">motacilla</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())


class TestM2MFieldComparison(TestCase):
    fixtures = ['test.json']
    comparison_class = compare.M2MFieldComparison

    def setUp(self):
        self.meetings_category = EventCategory.objects.create(name='Meetings')
        self.parties_category = EventCategory.objects.create(name='Parties')
        self.holidays_category = EventCategory.objects.create(name='Holidays')

    def test_hasnt_changed(self):
        christmas_event = EventPage.objects.get(url_path='/home/events/christmas/')
        saint_patrick_event = EventPage.objects.get(url_path='/home/events/saint-patrick/')

        christmas_event.categories = [self.meetings_category, self.parties_category]
        saint_patrick_event.categories = [self.meetings_category, self.parties_category]

        comparison = self.comparison_class(
            EventPage._meta.get_field('categories'), christmas_event, saint_patrick_event
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Categories")
        self.assertFalse(comparison.has_changed())
        self.assertEqual(comparison.htmldiff(), 'Meetings, Parties')
        self.assertIsInstance(comparison.htmldiff(), SafeString)

    def test_has_changed(self):
        christmas_event = EventPage.objects.get(url_path='/home/events/christmas/')
        saint_patrick_event = EventPage.objects.get(url_path='/home/events/saint-patrick/')

        christmas_event.categories = [self.meetings_category, self.parties_category]
        saint_patrick_event.categories = [self.meetings_category, self.holidays_category]

        comparison = self.comparison_class(
            EventPage._meta.get_field('categories'), christmas_event, saint_patrick_event
        )

        self.assertTrue(comparison.has_changed())
        self.assertEqual(comparison.htmldiff(), 'Meetings, <span class="deletion">Parties</span>, <span class="addition">Holidays</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)


class TestForeignObjectComparison(TestCase):
    comparison_class = compare.ForeignObjectComparison

    @classmethod
    def setUpTestData(cls):
        image_model = get_image_model()
        cls.test_image_1 = image_model.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )
        cls.test_image_2 = image_model.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )

    def test_hasnt_changed(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('feed_image'),
            EventPage(feed_image=self.test_image_1),
            EventPage(feed_image=self.test_image_1),
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Feed image")
        self.assertEqual(comparison.htmldiff(), 'Test image 1')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        comparison = self.comparison_class(
            EventPage._meta.get_field('feed_image'),
            EventPage(feed_image=self.test_image_1),
            EventPage(feed_image=self.test_image_2),
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Test image 1</span><span class="addition">Test image 2</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())


class TestForeignObjectComparisonWithCustomPK(TestCase):
    """ForeignObjectComparison works with models declaring a custom primary key field"""

    comparison_class = compare.ForeignObjectComparison

    @classmethod
    def setUpTestData(cls):
        ad1 = AdvertWithCustomPrimaryKey.objects.create(
            advert_id='ad1',
            text='Advert 1'
        )
        ad2 = AdvertWithCustomPrimaryKey.objects.create(
            advert_id='ad2',
            text='Advert 2'
        )
        cls.test_obj_1 = SnippetChooserModelWithCustomPrimaryKey.objects.create(
            advertwithcustomprimarykey=ad1
        )
        cls.test_obj_2 = SnippetChooserModelWithCustomPrimaryKey.objects.create(
            advertwithcustomprimarykey=ad2
        )

    def test_hasnt_changed(self):
        comparison = self.comparison_class(
            SnippetChooserModelWithCustomPrimaryKey._meta.get_field('advertwithcustomprimarykey'),
            self.test_obj_1,
            self.test_obj_1,
        )

        self.assertTrue(comparison.is_field)
        self.assertFalse(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), 'Advertwithcustomprimarykey')
        self.assertEqual(comparison.htmldiff(), 'Advert 1')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertFalse(comparison.has_changed())

    def test_has_changed(self):
        comparison = self.comparison_class(
            SnippetChooserModelWithCustomPrimaryKey._meta.get_field('advertwithcustomprimarykey'),
            self.test_obj_1,
            self.test_obj_2,
        )

        self.assertEqual(comparison.htmldiff(), '<span class="deletion">Advert 1</span><span class="addition">Advert 2</span>')
        self.assertIsInstance(comparison.htmldiff(), SafeString)
        self.assertTrue(comparison.has_changed())


class TestChildRelationComparison(TestCase):
    field_comparison_class = compare.FieldComparison
    comparison_class = compare.ChildRelationComparison

    def test_hasnt_changed(self):
        # Two event pages with speaker called "Father Christmas". Neither of
        # the speaker objects have an ID so this tests that the code can match
        # the two together by field content.
        event_page = EventPage(title="Event page", slug="event")
        event_page.speakers.add(EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        ))

        modified_event_page = EventPage(title="Event page", slug="event")
        modified_event_page.speakers.add(EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('speaker'),
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Speaker")
        self.assertFalse(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {0: 0})
        self.assertEqual(map_backwards, {0: 0})
        self.assertEqual(added, [])
        self.assertEqual(deleted, [])

    def test_has_changed(self):
        # Father Christmas renamed to Santa Claus. And Father Ted added.
        # Father Christmas should be mapped to Father Ted because they
        # are most alike. Santa claus should be displayed as "new"
        event_page = EventPage(title="Event page", slug="event")
        event_page.speakers.add(EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
            sort_order=0,
        ))

        modified_event_page = EventPage(title="Event page", slug="event")
        modified_event_page.speakers.add(EventPageSpeaker(
            first_name="Santa",
            last_name="Claus",
            sort_order=0,
        ))
        modified_event_page.speakers.add(EventPageSpeaker(
            first_name="Father",
            last_name="Ted",
            sort_order=1,
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('speaker'),
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Speaker")
        self.assertTrue(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {0: 1})  # Map Father Christmas to Father Ted
        self.assertEqual(map_backwards, {1: 0})  # Map Father Ted ot Father Christmas
        self.assertEqual(added, [0])  # Add Santa Claus
        self.assertEqual(deleted, [])

    def test_has_changed_with_same_id(self):
        # Father Christmas renamed to Santa Claus, but this time the ID of the
        # child object remained the same. It should now be detected as the same
        # object
        event_page = EventPage(title="Event page", slug="event")
        event_page.speakers.add(EventPageSpeaker(
            id=1,
            first_name="Father",
            last_name="Christmas",
            sort_order=0,
        ))

        modified_event_page = EventPage(title="Event page", slug="event")
        modified_event_page.speakers.add(EventPageSpeaker(
            id=1,
            first_name="Santa",
            last_name="Claus",
            sort_order=0,
        ))
        modified_event_page.speakers.add(EventPageSpeaker(
            first_name="Father",
            last_name="Ted",
            sort_order=1,
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('speaker'),
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Speaker")
        self.assertTrue(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {0: 0})  # Map Father Christmas to Santa Claus
        self.assertEqual(map_backwards, {0: 0})  # Map Santa Claus to Father Christmas
        self.assertEqual(added, [1])  # Add Father Ted
        self.assertEqual(deleted, [])

    def test_hasnt_changed_with_different_id(self):
        # Both of the child objects have the same field content but have a
        # different ID so they should be detected as separate objects
        event_page = EventPage(title="Event page", slug="event")
        event_page.speakers.add(EventPageSpeaker(
            id=1,
            first_name="Father",
            last_name="Christmas",
        ))

        modified_event_page = EventPage(title="Event page", slug="event")
        modified_event_page.speakers.add(EventPageSpeaker(
            id=2,
            first_name="Father",
            last_name="Christmas",
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('speaker'),
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Speaker")
        self.assertTrue(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {})
        self.assertEqual(map_backwards, {})
        self.assertEqual(added, [0])  # Add new Father Christmas
        self.assertEqual(deleted, [0])  # Delete old Father Christmas


class TestChildObjectComparison(TestCase):
    field_comparison_class = compare.FieldComparison
    comparison_class = compare.ChildObjectComparison

    def test_same_object(self):
        obj_a = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        )

        obj_b = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        )

        comparison = self.comparison_class(
            EventPageSpeaker,
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            obj_a,
            obj_b,
        )

        self.assertFalse(comparison.is_addition())
        self.assertFalse(comparison.is_deletion())
        self.assertFalse(comparison.has_changed())
        self.assertEqual(comparison.get_position_change(), 0)
        self.assertEqual(comparison.get_num_differences(), 0)

    def test_different_object(self):
        obj_a = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        )

        obj_b = EventPageSpeaker(
            first_name="Santa",
            last_name="Claus",
        )

        comparison = self.comparison_class(
            EventPageSpeaker,
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            obj_a,
            obj_b,
        )

        self.assertFalse(comparison.is_addition())
        self.assertFalse(comparison.is_deletion())
        self.assertTrue(comparison.has_changed())
        self.assertEqual(comparison.get_position_change(), 0)
        self.assertEqual(comparison.get_num_differences(), 2)

    def test_moved_object(self):
        obj_a = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
            sort_order=1,
        )

        obj_b = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
            sort_order=5,
        )

        comparison = self.comparison_class(
            EventPageSpeaker,
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            obj_a,
            obj_b,
        )

        self.assertFalse(comparison.is_addition())
        self.assertFalse(comparison.is_deletion())
        self.assertFalse(comparison.has_changed())
        self.assertEqual(comparison.get_position_change(), 4)
        self.assertEqual(comparison.get_num_differences(), 0)

    def test_addition(self):
        obj = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        )

        comparison = self.comparison_class(
            EventPageSpeaker,
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            None,
            obj,
        )

        self.assertTrue(comparison.is_addition())
        self.assertFalse(comparison.is_deletion())
        self.assertFalse(comparison.has_changed())
        self.assertIsNone(comparison.get_position_change(), 0)
        self.assertEqual(comparison.get_num_differences(), 0)

    def test_deletion(self):
        obj = EventPageSpeaker(
            first_name="Father",
            last_name="Christmas",
        )

        comparison = self.comparison_class(
            EventPageSpeaker,
            [
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('first_name')),
                partial(self.field_comparison_class, EventPageSpeaker._meta.get_field('last_name')),
            ],
            obj,
            None,
        )

        self.assertFalse(comparison.is_addition())
        self.assertTrue(comparison.is_deletion())
        self.assertFalse(comparison.has_changed())
        self.assertIsNone(comparison.get_position_change())
        self.assertEqual(comparison.get_num_differences(), 0)


class TestChildRelationComparisonUsingPK(TestCase):
    """Test related objects can be compred if they do not use id for primary key"""

    field_comparison_class = compare.FieldComparison
    comparison_class = compare.ChildRelationComparison

    def test_has_changed_with_same_id(self):
        # Head Count was changed but the PK of the child object remained the same.
        # It should be detected as the same object

        event_page = EventPage(title="Semi Finals", slug="semi-finals-2018")
        event_page.head_counts.add(HeadCountRelatedModelUsingPK(
            custom_id=1,
            head_count=22,
        ))

        modified_event_page = EventPage(title="Semi Finals", slug="semi-finals-2018")
        modified_event_page.head_counts.add(HeadCountRelatedModelUsingPK(
            custom_id=1,
            head_count=23,
        ))
        modified_event_page.head_counts.add(HeadCountRelatedModelUsingPK(
            head_count=25,
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('head_counts'),
            [partial(self.field_comparison_class, HeadCountRelatedModelUsingPK._meta.get_field('head_count'))],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), 'Head counts')
        self.assertTrue(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {0: 0})  # map head count 22 to 23
        self.assertEqual(map_backwards, {0: 0})  # map head count 23 to 22
        self.assertEqual(added, [1])  # add second head count
        self.assertEqual(deleted, [])

    def test_hasnt_changed_with_different_id(self):
        # Both of the child objects have the same field content but have a
        # different PK (ID) so they should be detected as separate objects
        event_page = EventPage(title="Finals", slug="finals-event-abc")
        event_page.head_counts.add(HeadCountRelatedModelUsingPK(
            custom_id=1,
            head_count=220
        ))

        modified_event_page = EventPage(title="Finals", slug="finals-event-abc")
        modified_event_page.head_counts.add(HeadCountRelatedModelUsingPK(
            custom_id=2,
            head_count=220
        ))

        comparison = self.comparison_class(
            EventPage._meta.get_field('head_counts'),
            [partial(self.field_comparison_class, HeadCountRelatedModelUsingPK._meta.get_field('head_count'))],
            event_page,
            modified_event_page,
        )

        self.assertFalse(comparison.is_field)
        self.assertTrue(comparison.is_child_relation)
        self.assertEqual(comparison.field_label(), "Head counts")
        self.assertTrue(comparison.has_changed())

        # Check mapping
        objs_a = list(comparison.val_a.all())
        objs_b = list(comparison.val_b.all())
        map_forwards, map_backwards, added, deleted = comparison.get_mapping(objs_a, objs_b)
        self.assertEqual(map_forwards, {})
        self.assertEqual(map_backwards, {})
        self.assertEqual(added, [0])  # Add new head count
        self.assertEqual(deleted, [0])  # Delete old head count
