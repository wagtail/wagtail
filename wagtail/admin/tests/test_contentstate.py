import json

from django.test import TestCase

from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter


def content_state_equal(v1, v2):
    "Test whether two contentState structures are equal, ignoring 'key' properties"
    if type(v1) != type(v2):
        return False

    if type(v1) == dict:
        if set(v1.keys()) != set(v2.keys()):
            return False
        return all(
            k == 'key' or content_state_equal(v, v2[k])
            for k, v in v1.items()
        )
    elif type(v1) == list:
        if len(v1) != len(v2):
            return False
        return all(
            content_state_equal(a, b) for a, b in zip(v1, v2)
        )
    else:
        return v1 == v2


class TestHtmlToContentState(TestCase):
    def assertContentStateEqual(self, v1, v2):
        "Assert that two contentState structures are equal, ignoring 'key' properties"
        self.assertTrue(content_state_equal(v1, v2), "%r does not match %r" % (v1, v2))

    def test_paragraphs(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Hello world!</p>
            <p>Goodbye world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_unknown_block_becomes_paragraph(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <foo>Hello world!</foo>
            <foo>I said hello world!</foo>
            <p>Goodbye world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'I said hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_bare_text_becomes_paragraph(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            before
            <p>paragraph</p>
            between
            <p>paragraph</p>
            after
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'before', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'paragraph', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'between', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'paragraph', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'after', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })
