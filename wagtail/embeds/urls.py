from django.urls import path

from wagtail.embeds.views import chooser


app_name = 'wagtailembeds'
urlpatterns = [
    path('chooser/', chooser.chooser, name='chooser'),
    path('chooser/upload/', chooser.chooser_upload, name='chooser_upload'),
]
