from rest_framework import serializers

from wagtail.models.pages import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"

    @staticmethod
    def natural_key(page: Page):
        return page.url_path
