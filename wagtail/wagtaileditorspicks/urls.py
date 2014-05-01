from django.conf.urls import url
from wagtail.wagtaileditorspicks.views import editorspicks, queries


urlpatterns = [
    url(r'^editorspicks/$', editorspicks.index, name='wagtaileditorspicks_editorspicks_index'),
    url(r'^editorspicks/add/$', editorspicks.add, name='wagtaileditorspicks_editorspicks_add'),
    url(r'^editorspicks/(\d+)/$', editorspicks.edit, name='wagtaileditorspicks_editorspicks_edit'),
    url(r'^editorspicks/(\d+)/delete/$', editorspicks.delete, name='wagtaileditorspicks_editorspicks_delete'),

    url(r'^queries/chooser/$', queries.chooser, name='wagtaileditorspicks_queries_chooser'),
    url(r'^queries/chooser/results/$', queries.chooserresults, name='wagtaileditorspicks_queries_chooserresults'),
]
