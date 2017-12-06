# Feature objects: these are mapped to feature identifiers within the rich text
# feature registry (wagtail.wagtailcore.rich_text.features). Each one implements
# a `construct_options` method which modifies an options dict as appropriate to
# enable that feature.

from draftjs_exporter.constants import ENTITY_TYPES


class BooleanFeature():
    """
    A feature which is enabled by a boolean flag at the top level of
    the options dict
    """
    def __init__(self, option_name):
        self.option_name = option_name

    def construct_options(self, options):
        options[self.option_name] = True


class ListFeature():
    """
    Abstract class for features that are defined in a list within the options dict.
    Subclasses must define option_name
    """
    def __init__(self, data):
        self.data = data

    def construct_options(self, options):
        if self.option_name not in options:
            options[self.option_name] = []

        options[self.option_name].append(self.data)


class EntityFeature(ListFeature):
    """A feature which is listed in the entityTypes list of the options"""
    option_name = 'entityTypes'


class BlockFeature(ListFeature):
    """A feature which is listed in the blockTypes list of the options"""
    option_name = 'blockTypes'


class InlineStyleFeature(ListFeature):
    """A feature which is listed in the inlineStyles list of the options"""
    option_name = 'inlineStyles'


class ImageFeature(EntityFeature):
    """
    Special case of EntityFeature so that we can easily define features that
    replicate the default 'image' feature with a custom list of image formats
    """
    def __init__(self, image_formats='__all__'):
        super().__init__({
            'label': 'Image',
            'type': ENTITY_TYPES.IMAGE,
            'icon': 'icon-image',
            'imageFormats': image_formats,
            'source': 'ImageSource',
            'decorator': 'Image',
        })
