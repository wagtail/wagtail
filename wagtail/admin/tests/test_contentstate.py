import json

from unittest.mock import patch

from django.test import TestCase
from draftjs_exporter.dom import DOM
from draftjs_exporter.html import HTML as HTMLExporter

from wagtail.admin.rich_text.converters.contentstate import (
    ContentstateConverter, persist_key_for_block)
from wagtail.embeds.models import Embed


def content_state_equal(v1, v2, match_keys=False):
    "Test whether two contentState structures are equal, ignoring 'key' properties if match_keys=False"
    if type(v1) != type(v2):
        return False

    if isinstance(v1, dict):
        if set(v1.keys()) != set(v2.keys()):
            return False
        return all(
            (k == 'key' and not match_keys) or content_state_equal(v, v2[k], match_keys=match_keys)
            for k, v in v1.items()
        )
    elif isinstance(v1, list):
        if len(v1) != len(v2):
            return False
        return all(
            content_state_equal(a, b, match_keys=match_keys) for a, b in zip(v1, v2)
        )
    else:
        return v1 == v2


class TestHtmlToContentState(TestCase):
    fixtures = ['test.json']

    def assertContentStateEqual(self, v1, v2, match_keys=False):
        "Assert that two contentState structures are equal, ignoring 'key' properties if match_keys is False"
        self.assertTrue(
            content_state_equal(v1, v2, match_keys=match_keys),
            "%s does not match %s" % (json.dumps(v1, indent=4), json.dumps(v2, indent=4))
        )

    def test_paragraphs(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p data-block-key='00000'>Hello world!</p>
            <p data-block-key='00001'>Goodbye world!</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00001', 'entityRanges': []},
            ]
        }, match_keys=True)

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
            <h1 data-block-key='00000'>The rules of Fight Club</h1>
            <ol>
                <li data-block-key='00001'>You do not talk about Fight Club.</li>
                <li data-block-key='00002'>You <b>do <em>not</em> talk</b> about Fight Club.</li>
            </ol>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'The rules of Fight Club', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00001', 'entityRanges': []},
                {
                    'inlineStyleRanges': [
                        {'offset': 4, 'length': 11, 'style': 'BOLD'}, {'offset': 7, 'length': 3, 'style': 'ITALIC'}
                    ],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00002', 'entityRanges': []
                },
            ]
        }, match_keys=True)

    def test_nested_list(self):
        converter = ContentstateConverter(features=['h1', 'ul'])
        result = json.loads(converter.from_database_format(
            '''
            <h1 data-block-key='00000'>Shopping list</h1>
            <ul>
                <li data-block-key='00001'>Milk</li>
                <li data-block-key='00002'>
                    Flour
                    <ul>
                        <li data-block-key='00003'>Plain</li>
                        <li data-block-key='00004'>Self-raising</li>
                    </ul>
                </li>
                <li data-block-key='00005'>Eggs</li>
            </ul>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Shopping list', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Milk', 'depth': 0, 'type': 'unordered-list-item', 'key': '00001', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Flour', 'depth': 0, 'type': 'unordered-list-item', 'key': '00002', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Plain', 'depth': 1, 'type': 'unordered-list-item', 'key': '00003', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Self-raising', 'depth': 1, 'type': 'unordered-list-item', 'key': '00004', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Eggs', 'depth': 0, 'type': 'unordered-list-item', 'key': '00005', 'entityRanges': []},
            ]
        }, match_keys=True)

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
                    'data': {
                        'id': 9999, 'url': None, 'parentId': None,
                    }
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an internal link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_link_to_root_page(self):
        converter = ContentstateConverter(features=['link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>an <a linktype="page" id="1">internal</a> link</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {
                '0': {
                    'mutability': 'MUTABLE', 'type': 'LINK',
                    'data': {'id': 1, 'url': None, 'parentId': None}
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
                    'data': {'id': 9999}
                }
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'a document link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 2, 'length': 8, 'key': 0}]
                },
            ]
        })

    def test_document_link_with_missing_id(self):
        converter = ContentstateConverter(features=['document-link'])
        result = json.loads(converter.from_database_format(
            '''
            <p>a <a linktype="document">document</a> link</p>
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

    def test_collapse_targeted_whitespace_characters(self):
        # We expect all targeted whitespace characters (one or more consecutively)
        # to be replaced by a single space. (\xa0 is a non-breaking whitespace)
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>Multiple whitespaces:     should  be reduced</p>
            <p>Multiple non-breaking whitespace characters:  \xa0\xa0\xa0  should be preserved</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Multiple whitespaces: should be reduced', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Multiple non-breaking whitespace characters: \xa0\xa0\xa0 should be preserved', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_extra_end_tag_before(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            </p>
            <p>Before</p>
            '''
        ))
        # The leading </p> tag should be ignored instead of blowing up with a
        # pop from empty list error
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Before', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_extra_end_tag_after(self):
        converter = ContentstateConverter(features=[])
        result = json.loads(converter.from_database_format(
            '''
            <p>After</p>
            </p>
            '''
        ))
        # The tailing </p> tag should be ignored instead of blowing up with a
        # pop from empty list error
        self.assertContentStateEqual(result, {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'After', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
            ]
        })

    def test_p_with_class(self):
        # Test support for custom conversion rules which require correct treatment of
        # CSS precedence in HTMLRuleset. Here, <p class="intro"> should match the
        # 'p[class="intro"]' rule rather than 'p' and thus become an 'intro-paragraph' block
        converter = ContentstateConverter(features=['intro'])
        result = json.loads(converter.from_database_format(
            '''
            <p class="intro">before</p>
            <p>after</p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'intro-paragraph'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'}
            ],
            'entityMap': {}
        })

    def test_image_inside_paragraph(self):
        # In Draftail's data model, images are block-level elements and therefore
        # split up preceding / following text into their own paragraphs
        converter = ContentstateConverter(features=['image'])
        result = json.loads(converter.from_database_format(
            '''
            <p>before <embed embedtype="image" alt="an image" id="1" format="left" /> after</p>
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

    def test_image_inside_style(self):
        # https://github.com/wagtail/wagtail/issues/4602 - ensure that an <embed> inside
        # an inline style is handled. This is not valid in Draftail as images are block-level,
        # but should be handled without errors, splitting the image into its own block
        converter = ContentstateConverter(features=['image', 'italic'])
        result = json.loads(converter.from_database_format(
            '''
            <p><i>before <embed embedtype="image" alt="an image" id="1" format="left" /> after</i></p>
            <p><i><embed embedtype="image" alt="an image" id="1" format="left" /></i></p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [{'offset': 0, 'length': 6, 'style': 'ITALIC'}], 'entityRanges': [], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [{'offset': 0, 'length': 5, 'style': 'ITALIC'}], 'entityRanges': [], 'depth': 0, 'text': 'after', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [{'offset': 0, 'length': 0, 'style': 'ITALIC'}], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [{'offset': 0, 'length': 0, 'style': 'ITALIC'}], 'entityRanges': [], 'depth': 0, 'text': '', 'type': 'unstyled'},
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

    def test_image_inside_link(self):
        # https://github.com/wagtail/wagtail/issues/4602 - ensure that an <embed> inside
        # a link is handled. This is not valid in Draftail as images are block-level,
        # but should be handled without errors, splitting the image into its own block
        converter = ContentstateConverter(features=['image', 'link'])
        result = json.loads(converter.from_database_format(
            '''
            <p><a href="https://wagtail.io">before <embed embedtype="image" alt="an image" id="1" format="left" /> after</a></p>
            <p><a href="https://wagtail.io"><embed embedtype="image" alt="an image" id="1" format="left" /></a></p>
            '''
        ))
        self.assertContentStateEqual(result, {
            'blocks': [
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 6}], 'depth': 0, 'text': 'before', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 1, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 0, 'offset': 0, 'length': 5}], 'depth': 0, 'text': 'after', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 2, 'offset': 0, 'length': 0}], 'depth': 0, 'text': '', 'type': 'unstyled'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 3, 'offset': 0, 'length': 1}], 'depth': 0, 'text': ' ', 'type': 'atomic'},
                {'key': '00000', 'inlineStyleRanges': [], 'entityRanges': [{'key': 2, 'offset': 0, 'length': 0}], 'depth': 0, 'text': '', 'type': 'unstyled'},
            ],
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'https://wagtail.io'}},
                '1': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                },
                '2': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': 'https://wagtail.io'}},
                '3': {
                    'data': {'format': 'left', 'alt': 'an image', 'id': '1', 'src': '/media/not-found'},
                    'mutability': 'IMMUTABLE', 'type': 'IMAGE'
                },
            }
        })


class TestContentStateToHtml(TestCase):
    def test_external_link(self):
        converter = ContentstateConverter(features=['link'])
        contentstate_json = json.dumps({
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

        result = converter.to_database_format(contentstate_json)
        self.assertEqual(result, '<p data-block-key="00000">an <a href="http://wagtail.io">external</a> link</p>')

    def test_local_link(self):
        converter = ContentstateConverter(features=['link'])
        contentstate_json = json.dumps({
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': '/some/local/path/'}}
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

        result = converter.to_database_format(contentstate_json)
        self.assertEqual(result, '<p data-block-key="00000">an <a href="/some/local/path/">external</a> link</p>')

    def test_reject_javascript_link(self):
        converter = ContentstateConverter(features=['link'])
        contentstate_json = json.dumps({
            'entityMap': {
                '0': {'mutability': 'MUTABLE', 'type': 'LINK', 'data': {'url': "javascript:alert('oh no')"}}
            },
            'blocks': [
                {
                    'inlineStyleRanges': [], 'text': 'an external link', 'depth': 0, 'type': 'unstyled', 'key': '00000',
                    'entityRanges': [{'offset': 3, 'length': 8, 'key': 0}]
                },
            ]
        })

        result = converter.to_database_format(contentstate_json)
        self.assertEqual(result, '<p data-block-key="00000">an <a>external</a> link</p>')

    def test_paragraphs_retain_keys(self):
        converter = ContentstateConverter(features=[])
        contentState = json.dumps({
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00001', 'entityRanges': []},
            ]
        })
        result = converter.to_database_format(contentState)
        self.assertHTMLEqual(result, '''
            <p data-block-key='00000'>Hello world!</p>
            <p data-block-key='00001'>Goodbye world!</p>
            ''')

    def test_wrapped_block_retains_key(self):
        # Test a block which uses a wrapper correctly receives the key defined on the inner element
        converter = ContentstateConverter(features=['h1', 'ol', 'bold', 'italic'])
        result = converter.to_database_format(json.dumps({
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'The rules of Fight Club', 'depth': 0, 'type': 'header-one', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00001', 'entityRanges': []},
                {
                    'inlineStyleRanges': [],
                    'text': 'You do not talk about Fight Club.', 'depth': 0, 'type': 'ordered-list-item', 'key': '00002', 'entityRanges': []
                },
            ]
        }))
        self.assertHTMLEqual(result, '''
            <h1 data-block-key='00000'>The rules of Fight Club</h1>
            <ol>
                <li data-block-key='00001'>You do not talk about Fight Club.</li>
                <li data-block-key='00002'>You do not talk about Fight Club.</li>
            </ol>
        ''')

    def test_wrap_block_function(self):
        # Draft JS exporter's block_map config can also contain a function to handle a particular block
        # Test that persist_key_for_block still works with such a function, making the resultant conversion
        # keep the same block key between html and contentstate
        exporter_config = {
            'block_map': {
                'unstyled': persist_key_for_block(lambda props: DOM.create_element('p', {}, props['children'])),
            },
            'style_map': {},
            'entity_decorators': {},
            'composite_decorators': [],
            'engine': DOM.STRING,
        }
        contentState = {
            'entityMap': {},
            'blocks': [
                {'inlineStyleRanges': [], 'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []},
                {'inlineStyleRanges': [], 'text': 'Goodbye world!', 'depth': 0, 'type': 'unstyled', 'key': '00001', 'entityRanges': []},
            ]
        }
        result = HTMLExporter(exporter_config).render(contentState)
        self.assertHTMLEqual(result, '''
            <p data-block-key='00000'>Hello world!</p>
            <p data-block-key='00001'>Goodbye world!</p>
            ''')

    def test_style_fallback(self):
        # Test a block which uses an invalid inline style, and will be removed
        converter = ContentstateConverter(features=[])

        with self.assertLogs(level='WARNING') as log_output:
            result = converter.to_database_format(json.dumps({
                'entityMap': {},
                'blocks': [
                    {
                        'inlineStyleRanges': [{'offset': 0, 'length': 12, 'style': 'UNDERLINE'}],
                        'text': 'Hello world!', 'depth': 0, 'type': 'unstyled', 'key': '00000', 'entityRanges': []
                    },
                ]
            }))

        self.assertHTMLEqual(result, '''
            <p data-block-key="00000">
                Hello world!
            </p>
        ''')
        self.assertIn(
            'Missing config for "UNDERLINE". Deleting style.',
            log_output.output[0]
        )
