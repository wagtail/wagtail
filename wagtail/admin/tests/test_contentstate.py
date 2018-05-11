import json

from django.test import TestCase
from mock import patch

from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.embeds.models import Embed


def content_state_equal(v1, v2):
    "Test whether two contentState structures are equal, ignoring 'key' properties"
    if type(v1) != type(v2):
        return False

    if isinstance(v1, dict):
        if set(v1.keys()) != set(v2.keys()):
            return False
        return all(
            k == 'key' or content_state_equal(v, v2[k])
            for k, v in v1.items()
        )
    elif isinstance(v1, list):
        if len(v1) != len(v2):
            return False
        return all(
            content_state_equal(a, b) for a, b in zip(v1, v2)
        )
    else:
        return v1 == v2


class TestHtmlToContentState(TestCase):
    fixtures = ['test.json']

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

    def test_ignore_unrecognised_tags_in_blocks(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Hello <foo>frabjuous</foo> world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello frabjuous world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_inline_styles(self):
        converter = ContentstateConverter(features=['bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            <p>You <b>do <em>not</em> talk</b> about Fight Club.</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_inline_styles_at_top_level(self):
        converter = ContentstateConverter(features=['bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            You <b>do <em>not</em> talk</b> about Fight Club.
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_inline_styles_at_start_of_bare_block(self):
        converter = ContentstateConverter(features=['bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''<b>Seriously</b>, stop talking about <i>Fight Club</i> already.'''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 0, 'length': 9, 'style': 'BOLD'},
                        {'offset': 30, 'length': 10, 'style': 'ITALIC'},
                    ],
                    'text': 'Seriously, stop talking about Fight Club already.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_inline_styles_depend_on_features(self):
        converter = ContentstateConverter(features=['italic', 'just-made-it-up'])
        result = json.loads(converter.from_database_format(
            '''
            <p>You <b>do <em>not</em> talk</b> about Fight Club.</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {
                    'inlineStyleRanges': [
                        {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_ordered_list(self):
        converter = ContentstateConverter(features=['h1', 'ol', 'bold', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            <h1>The rules of Fight Club</h1>
            <ol>
                <li>You do not talk about Fight Club.</li>
                <li>You <b>do <em>not</em> talk</b> about Fight Club.</li>
            </ol>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'The rules of Fight Club', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00000', 'entityRanges': []},
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00000', 'entityRanges': []
                },
            ]
        })

    def test_nested_list(self):
        converter = ContentstateConverter(features=['h1', 'ul'])
        result = json.loads(converter.from_database_format(
            '''
            <h1>Shopping list</h1>
            <ul>
                <li>Milk</li>
                <li>
                    Flour
                    <ul>
                        <li>Plain</li>
                        <li>Self-raising</li>
                    </ul>
                </li>
                <li>Eggs</li>
            </ul>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Shopping list', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Milk', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Flour', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Plain', 'depth': 1, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Self-raising', 'depth': 1, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Eggs', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_external_link(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>an <a href="http://wagtail.io">external</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'http://wagtail.io'}}
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_link_in_bare_text(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''an <a href="http://wagtail.io">external</a> link'''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'http://wagtail.io'}}
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_link_at_start_of_bare_text(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''<a href="http://wagtail.io">an external link</a> and <a href="http://torchbox.com">another</a>'''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'http://wagtail.io'}},
                '1': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'http://torchbox.com'}},
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link and another', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [
                        {'offset': 0, 'length': 16, 'key': 0},
                        {'offset': 21, 'length': 7, 'key': 1},
                    ]
                },
            ]
        })

    def test_page_link(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>an <a linktype="page" id="3">internal</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'mutability': 'MUTABLE', 'type': 'LINK',
                    'data': {'id': 3, 'url': '/events/', 'parentId': 2}
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an internal link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_broken_page_link(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>an <a linktype="page" id="9999">internal</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'mutability': 'MUTABLE', 'type': 'LINK',
                    'data': {}
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an internal link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_document_link(self):
        converter = ContentstateConverter(features=['document-link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>a <a linktype="document" id="1">document</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'mutability': 'MUTABLE', 'type': 'DOCUMENT',
                    'data': {'id': 1, 'url': '/documents/1/test.pdf', 'filename': 'test.pdf'}
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'a document link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 2, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_broken_document_link(self):
        converter = ContentstateConverter(features=['document-link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>a <a linktype="document" id="9999">document</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'mutability': 'MUTABLE', 'type': 'DOCUMENT',
                    'data': {}
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'a document link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 2, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_image_embed(self):
        converter = ContentstateConverter(features=['image'])
        result = json.loads(converter.from_database_format(
            '''
            <p>before</p>
            <embed embedtype="image" alt="an image" id="1" format="left" />
            <p>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
            'entityMap': {
                '0': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                }
            }
        })

    def test_add_spacer_paragraph_between_image_embeds(self):
        converter = ContentstateConverter(features=['image'])
        result = json.loads(converter.from_database_format(
            '''
            <embed embedtype="image" alt="an image" id="1" format="left" />
            <embed embedtype="image" alt="an image" id="1" format="left" />
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
            ],
            'entityMap': {
                '0': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                },
                '1': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                },
            }
        })

    def test_image_after_list(self):
        """
        There should be no spacer paragraph inserted between a list and an image
        """
        converter = ContentstateConverter(features=['ul', 'image'])
        result = json.loads(converter.from_database_format(
            '''
            <ul>
                <li>Milk</li>
                <li>Eggs</li>
            </ul>
            <embed embedtype="image" alt="an image" id="1" format="left" />
            <ul>
                <li>More milk</li>
                <li>More eggs</li>
            </ul>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                },
            },
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Milk', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Eggs', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'inlineStyleRanges': [], 'text': 'More milk', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'More eggs', 'depth': 0, 'type': 'unordered-list-item', 'key': '00000', 'entityRanges': []},
            ]
        })

    @patch('wagtail.embeds.embeds.get_embed')
    def test_media_embed(self, get_embed):
        get_embed.return_value = Embed(
            url='https://www.youtube.com/watch?v=Kh0Y2hVe_bw',
            max_width=None,
            type='video',
            html='test html',
            title='what are birds',
            author_name='look around you',
            provider_name='YouTube',
            thumbnail_url='http://test/thumbnail.url',
            width=1000,
            height=1000,
        )

        converter = ContentstateConverter(features=['embed'])
        result = json.loads(converter.from_database_format(
            '''
            <p>before</p>
            <embed embedtype="media" url="https://www.youtube.com/watch?v=Kh0Y2hVe_bw" />
            <p>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
            'entityMap': {
                '0': {
                    'data': {
                        'thumbnail': 'http://test/thumbnail.url',
                        'embedType': 'video',
                        'providerName': 'YouTube',
                        'title': 'what are birds',
                        'authorName': 'look around you',
                        'url': 'https://www.youtube.com/watch?v=Kh0Y2hVe_bw'
                    },
                    'mutability': 'IMMUTABLE', 'type': 'EMBED'
                }
            }
        })

    @patch('wagtail.embeds.embeds.get_embed')
    def test_add_spacer_paras_between_media_embeds(self, get_embed):
        get_embed.return_value = Embed(
            url='https://www.youtube.com/watch?v=Kh0Y2hVe_bw',
            max_width=None,
            type='video',
            html='test html',
            title='what are birds',
            author_name='look around you',
            provider_name='YouTube',
            thumbnail_url='http://test/thumbnail.url',
            width=1000,
            height=1000,
        )

        converter = ContentstateConverter(features=['embed'])
        result = json.loads(converter.from_database_format(
            '''
            <embed embedtype="media" url="https://www.youtube.com/watch?v=Kh0Y2hVe_bw" />
            <embed embedtype="media" url="https://www.youtube.com/watch?v=Kh0Y2hVe_bw" />
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
            ],
            'entityMap': {
                '0': {
                    'data': {
                        'thumbnail': 'http://test/thumbnail.url',
                        'embedType': 'video',
                        'providerName': 'YouTube',
                        'title': 'what are birds',
                        'authorName': 'look around you',
                        'url': 'https://www.youtube.com/watch?v=Kh0Y2hVe_bw'
                    },
                    'mutability': 'IMMUTABLE', 'type': 'EMBED'
                },
                '1': {
                    'data': {
                        'thumbnail': 'http://test/thumbnail.url',
                        'embedType': 'video',
                        'providerName': 'YouTube',
                        'title': 'what are birds',
                        'authorName': 'look around you',
                        'url': 'https://www.youtube.com/watch?v=Kh0Y2hVe_bw'
                    },
                    'mutability': 'IMMUTABLE', 'type': 'EMBED'
                },
            }
        })

    def test_hr(self):
        converter = ContentstateConverter(features=['hr'])
        result = json.loads(converter.from_database_format(
            '''
            <p>before</p>
            <hr />
            <p>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
            'entityMap': {
                '0': {
                    'data': {},
                    'mutability': 'IMMUTABLE', 'type': 'HORIZONTAL_RULE'
                }
            }
        })

    def test_add_spacer_paragraph_between_hrs(self):
        converter = ContentstateConverter(features=['hr'])
        result = json.loads(converter.from_database_format(
            '''
            <hr />
            <hr />
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
            ],
            'entityMap': {
                '0': {
                    'data': {},
                    'mutability': 'IMMUTABLE', 'type': 'HORIZONTAL_RULE'
                },
                '1': {
                    'data': {},
                    'mutability': 'IMMUTABLE', 'type': 'HORIZONTAL_RULE'
                },
            }
        })

    def test_block_element_in_paragraph(self):
        converter = ContentstateConverter(features=['hr'])
        result = json.loads(converter.from_database_format(
            '''
            <p>before<hr />after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
            'entityMap': {
                '0': {
                    'data': {},
                    'mutability': 'IMMUTABLE', 'type': 'HORIZONTAL_RULE'
                }
            }
        })

    def test_br_element_in_paragraph(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>before<br/>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before\nafter',
                 'type': 'unstyled'}
            ],
        })

    def test_br_element_between_paragraphs(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>before</p>
            <br />
            <p>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
        })

    def test_block_element_in_empty_paragraph(self):
        converter = ContentstateConverter(features=['hr'])
        result = json.loads(converter.from_database_format(
            '''
            <p><hr /></p>
            '''
        ))
        # ignoring the paragraph completely would probably be better,
        # but we'll settle for an empty preceding paragraph and not crashing as the next best thing...
        # (and if it's the first/last block we actually do want a spacer paragraph anyhow)
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
            ],
            'entityMap': {
                '0': {
                    'data': {},
                    'mutability': 'IMMUTABLE', 'type': 'HORIZONTAL_RULE'
                }
            }
        })

    def test_html_entities(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Arthur &quot;two sheds&quot; Jackson &lt;the third&gt; &amp; his wife</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Arthur "two sheds" Jackson <the third> & his wife', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })
