from django.conf.urls import url
from wagtail.wagtailsearch.views import editorspicks, queries


urlpatterns = [
    url(r"^editorspicks/$", editorspicks.index, name="wagtailsearch_editorspicks_index"),
    url(r"^editorspicks/add/$", editorspicks.add, name="wagtailsearch_editorspicks_add"),
    url(r"^editorspicks/(\d+)/$", editorspicks.edit, name="wagtailsearch_editorspicks_edit"),
    url(r"^editorspicks/(\d+)/delete/$", editorspicks.delete, name="wagtailsearch_editorspicks_delete"),

    url(r"^queries/chooser/$", queries.chooser, name="wagtailsearch_queries_chooser"),
    url(r"^queries/chooser/results/$", queries.chooserresults, name="wagtailsearch_queries_chooserresults"),
]
