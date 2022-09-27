from wagtail.snippets.views.snippets import SnippetViewSet
from wagtail.test.snippets.models import FilterableSnippetFilterSet


class FilterableSnippetViewSet(SnippetViewSet):
    filterset_class = FilterableSnippetFilterSet
