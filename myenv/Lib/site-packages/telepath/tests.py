import itertools

from django.utils.translation import activate, gettext_lazy
from unittest import TestCase

from telepath import Adapter, JSContext, register, StringAdapter


class Artist:
    def __init__(self, name):
        self.name = name


@register
class Album:
    def __init__(self, title, artists):
        self.title = title
        self.artists = artists

    def telepath_pack(self, context):
        context.add_media(js='music_player.js')

        return ('music.Album', [self.title, self.artists])


class ArtistAdapter(Adapter):
    js_constructor = 'music.Artist'

    def js_args(self, obj):
        return [obj.name]


register(ArtistAdapter(), Artist)


class TestPacking(TestCase):
    def test_pack_object(self):
        beyonce = Artist("Beyoncé")
        ctx = JSContext()
        result = ctx.pack(beyonce)

        self.assertEqual(result, {'_type': 'music.Artist', '_args': ["Beyoncé"]})

    def test_pack_list(self):
        destinys_child = [
            Artist("Beyoncé"), Artist("Kelly Rowland"), Artist("Michelle Williams")
        ]
        ctx = JSContext()
        result = ctx.pack(destinys_child)

        self.assertEqual(result, [
            {'_type': 'music.Artist', '_args': ["Beyoncé"]},
            {'_type': 'music.Artist', '_args': ["Kelly Rowland"]},
            {'_type': 'music.Artist', '_args': ["Michelle Williams"]},
        ])

    def test_pack_dict(self):
        glastonbury = {
            'pyramid_stage': Artist("Beyoncé"),
            'acoustic_stage': Artist("Ed Sheeran"),
        }
        ctx = JSContext()
        result = ctx.pack(glastonbury)
        self.assertEqual(result, {
            'pyramid_stage': {'_type': 'music.Artist', '_args': ["Beyoncé"]},
            'acoustic_stage': {'_type': 'music.Artist', '_args': ["Ed Sheeran"]},
        })

    def test_dict_reserved_words(self):
        profile = {
            '_artist': Artist("Beyoncé"),
            '_type': 'R&B',
        }
        ctx = JSContext()
        result = ctx.pack(profile)

        self.assertEqual(result, {
            '_dict': {
                '_artist': {'_type': 'music.Artist', '_args': ["Beyoncé"]},
                '_type': 'R&B',
            }
        })

    def test_recursive_arg_packing(self):
        dangerously_in_love = Album("Dangerously in Love", [
            Artist("Beyoncé"),
        ])
        ctx = JSContext()
        result = ctx.pack(dangerously_in_love)

        self.assertEqual(result, {
            '_type': 'music.Album',
            '_args': [
                "Dangerously in Love",
                [
                    {'_type': 'music.Artist', '_args': ["Beyoncé"]},
                ]
            ]
        })

        self.assertIn('music_player.js', str(ctx.media))

    def test_object_references(self):
        beyonce = Artist("Beyoncé")
        jay_z = Artist("Jay-Z")
        discography = [
            Album("Dangerously in Love", [beyonce]),
            Album("Everything Is Love", [beyonce, jay_z]),
        ]
        ctx = JSContext()
        result = ctx.pack(discography)

        self.assertEqual(result, [
            {
                '_type': 'music.Album',
                '_args': [
                    "Dangerously in Love",
                    [
                        {'_type': 'music.Artist', '_args': ["Beyoncé"], '_id': 0},
                    ]
                ]
            },
            {
                '_type': 'music.Album',
                '_args': [
                    "Everything Is Love",
                    [
                        {'_ref': 0},
                        {'_type': 'music.Artist', '_args': ["Jay-Z"]},
                    ]
                ]
            },
        ])

        self.assertIn('music_player.js', str(ctx.media))

    def test_list_references(self):
        destinys_child = [
            Artist("Beyoncé"), Artist("Kelly Rowland"), Artist("Michelle Williams")
        ]
        discography = [
            Album("Destiny's Child", destinys_child),
            Album("Survivor", destinys_child),
        ]
        ctx = JSContext()
        result = ctx.pack(discography)

        self.assertEqual(result, [
            {
                '_type': 'music.Album',
                '_args': [
                    "Destiny's Child",
                    {
                        '_list': [
                            {'_type': 'music.Artist', '_args': ["Beyoncé"]},
                            {'_type': 'music.Artist', '_args': ["Kelly Rowland"]},
                            {'_type': 'music.Artist', '_args': ["Michelle Williams"]},
                        ],
                        '_id': 0,
                    }
                ]
            },
            {
                '_type': 'music.Album',
                '_args': [
                    "Survivor",
                    {'_ref': 0},
                ]
            },
        ])

    def test_primitive_value_references(self):
        beyonce_name = "Beyoncé Giselle Knowles-Carter"
        beyonce = Artist(beyonce_name)
        discography = [
            Album("Dangerously in Love", [beyonce]),
            Album(beyonce_name, [beyonce]),
        ]
        ctx = JSContext()
        result = ctx.pack(discography)

        self.assertEqual(result, [
            {
                '_type': 'music.Album',
                '_args': [
                    "Dangerously in Love",
                    [
                        {
                            '_type': 'music.Artist',
                            '_args': [{'_val': "Beyoncé Giselle Knowles-Carter", '_id': 0}],
                            '_id': 1,
                        },
                    ]
                ]
            },
            {
                '_type': 'music.Album',
                '_args': [
                    {'_ref': 0},
                    [
                        {'_ref': 1},
                    ]
                ]
            },
        ])

    def test_avoid_primitive_value_references_for_short_strings(self):
        beyonce_name = "Beyoncé"
        beyonce = Artist(beyonce_name)
        discography = [
            Album("Dangerously in Love", [beyonce]),
            Album(beyonce_name, [beyonce]),
        ]
        ctx = JSContext()
        result = ctx.pack(discography)

        self.assertEqual(result, [
            {
                '_type': 'music.Album',
                '_args': [
                    "Dangerously in Love",
                    [
                        {
                            '_type': 'music.Artist',
                            '_args': ["Beyoncé"],
                            '_id': 1,
                        },
                    ]
                ]
            },
            {
                '_type': 'music.Album',
                '_args': [
                    "Beyoncé",
                    [
                        {'_ref': 1},
                    ]
                ]
            },
        ])

    def test_lazy_translation_objects(self):
        yes = Artist(gettext_lazy("Yes"))

        activate('en')
        ctx = JSContext()
        result = ctx.pack(yes)
        self.assertEqual(result, {'_type': 'music.Artist', '_args': ["Yes"]})

        activate('fr')
        ctx = JSContext()
        result = ctx.pack(yes)
        self.assertEqual(result, {'_type': 'music.Artist', '_args': ["Oui"]})


class Ark:
    def __init__(self, animals):
        self.animals = animals

    def animals_by_type(self):
        return itertools.groupby(self.animals, lambda animal: animal['type'])


class ArkAdapter(Adapter):
    js_constructor = 'boats.Ark'

    def js_args(self, obj):
        return [obj.animals_by_type()]


register(ArkAdapter(), Ark)


class TestIDCollisions(TestCase):
    def test_grouper_object_collisions(self):
        """
        Certain functions such as itertools.groupby will cause new objects (namely, tuples and
        custom itertools._grouper iterables) to be created in the course of iterating over the
        object tree. If we're not careful, these will be released and the memory reallocated to
        new objects while we're still iterating, leading to ID collisions.
        """
        # create 100 Ark objects all with distinct animals (no object references are re-used)
        arks = [
            Ark([
                {'type': 'lion', 'name': 'Simba %i' % i}, {'type': 'lion', 'name': 'Nala %i' % i},
                {'type': 'dog', 'name': 'Lady %i' % i}, {'type': 'dog', 'name': 'Tramp %i' % i},
            ])
            for i in range(0, 100)
        ]

        ctx = JSContext()
        result = ctx.pack(arks)

        self.assertEqual(len(result), 100)
        for i, ark in enumerate(result):
            # each object should be represented in full, with no _id or _ref keys
            self.assertEqual(ark, {
                '_type': 'boats.Ark',
                '_args': [
                    [
                        ['lion', [{'type': 'lion', 'name': 'Simba %i' % i}, {'type': 'lion', 'name': 'Nala %i' % i}]],
                        ['dog', [{'type': 'dog', 'name': 'Lady %i' % i}, {'type': 'dog', 'name': 'Tramp %i' % i}]],
                    ]
                ]
            })


class StringLike():
    def __init__(self, val):
        self.val = val.upper()

    def __str__(self):
        return self.val


class StringLikeAdapter(StringAdapter):
    def build_node(self, obj, context):
        return super().build_node(str(obj), context)


register(StringLikeAdapter(), StringLike)


class TestPackingToString(TestCase):
    def test_pack_to_string(self):
        val = [
            "real string",
            StringLike("stringlike"),
        ]

        ctx = JSContext()
        result = ctx.pack(val)

        self.assertEqual(result, ["real string", "STRINGLIKE"])
