from wagtail.wagtailsearch.backends.base import BaseSearch


class DummySearch(BaseSearch):
    pass


class NoUpdateSearch(BaseSearch):
    update_required = False


SearchBackend = DummySearch
