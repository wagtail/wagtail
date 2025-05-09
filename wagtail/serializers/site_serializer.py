from rest_framework import serializers

from wagtail.models.sites import Site


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = "__all__"

    @staticmethod
    def natural_key(site: Site):
        return (site.hostname, site.port)
