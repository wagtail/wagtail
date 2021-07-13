import sys

from wagtail.utils.deprecation import MovedDefinitionHandler, RemovedInWagtail216Warning


# If users still import their backend from here, they will get a deprecation warning. The actual backend implementation is now in a submodule (database).


MOVED_DEFINITIONS = {
    'DatabaseSearchQueryCompiler': ('wagtail.search.backends.database', 'DatabaseSearchQueryCompiler'),
    'DatabaseSearchResults': ('wagtail.search.backends.database', 'DatabaseSearchResults'),
    'DatabaseSearchBackend': ('wagtail.search.backends.database', 'DatabaseSearchBackend'),
    'SearchBackend': ('wagtail.search.backends.database', 'SearchBackend'),
}

sys.modules[__name__] = MovedDefinitionHandler(sys.modules[__name__], MOVED_DEFINITIONS, RemovedInWagtail216Warning)
