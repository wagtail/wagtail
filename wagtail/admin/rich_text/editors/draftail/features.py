from django.forms import Media

# Feature objects: these are mapped to feature identifiers within the rich text
# feature registry (wagtail.core.rich_text.features). Each one implements
# a `construct_options` method which modifies an options dict as appropriate to
# enable that feature.

# Additionally, a Feature object defines a media property
# (https://docs.djangoproject.com/en/stable/topics/forms/media/) to specify css/js
# files to import when the feature is active.


class Feature:
    def __init__(self, js=None, css=None):
        self.js = js
        self.css = css

    @property
    def media(self):
        return Media(js=self.js, css=self.css)


class BooleanFeature(Feature):
    """
    A feature which is enabled by a boolean flag at the top level of
    the options dict
    """
    def __init__(self, option_name, **kwargs):
        super().__init__(**kwargs)
        self.option_name = option_name

    def construct_options(self, options):
        options[self.option_name] = True


class ListFeature(Feature):
    """
    Abstract class for features that are defined in a list within the options dict.
    Subclasses must define option_name
    """
    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
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
