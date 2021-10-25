from warnings import warn

from wagtail.search.backends.database.fallback import (  # noqa
    DatabaseSearchBackend, DatabaseSearchQueryCompiler, DatabaseSearchResults, SearchBackend)
from wagtail.utils.deprecation import RemovedInWagtail217Warning


warn(
    "The wagtail.search.backends.db search backend is deprecated and has been replaced by "
    "wagtail.search.backends.database. "
    "See https://docs.wagtail.io/en/stable/releases/2.15.html#database-search-backends-replaced",
    category=RemovedInWagtail217Warning
)
