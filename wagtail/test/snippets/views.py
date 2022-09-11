from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.test.snippets.models import FilterableSnippetFilterSet


class FilterableSnippetViewSet(SnippetViewSet):
    filterset_class = FilterableSnippetFilterSet
    list_display = ["text", "country_code", "get_foo_country_code", UpdatedAtColumn()]
