from wagtail.admin.forms.models import WagtailAdminModelForm

from .models import Publisher


class PublisherModelAdminForm(WagtailAdminModelForm):
    class Meta:
        model = Publisher
        fields = ["name"]
