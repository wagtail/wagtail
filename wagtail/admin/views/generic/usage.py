from django.contrib.admin.utils import quote
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.ui import tables
from wagtail.admin.utils import get_latest_str
from wagtail.admin.widgets.button import HeaderButton
from wagtail.models import DraftStateMixin, ReferenceIndex

from .base import BaseListingView, BaseObjectMixin
from .permissions import PermissionCheckedMixin


class TitleColumn(tables.TitleColumn):
    def get_link_attrs(self, instance, parent_context):
        return {"title": instance["edit_link_title"]}


class UsageView(PermissionCheckedMixin, BaseObjectMixin, BaseListingView):
    paginate_by = 20
    page_title = gettext_lazy("Usage")
    index_url_name = None
    edit_url_name = None
    usage_url_name = None
    permission_required = "change"

    @cached_property
    def describe_on_delete(self):
        return bool(self.request.GET.get("describe_on_delete"))

    def get_object(self):
        object = super().get_object()
        if isinstance(object, DraftStateMixin):
            return object.get_latest_revision_as_object()
        return object

    def get_edit_url(self, instance):
        if self.edit_url_name:
            return reverse(self.edit_url_name, args=(quote(instance.pk),))

    def get_usage_url(self, instance):
        if self.usage_url_name:
            return reverse(self.usage_url_name, args=(quote(instance.pk),))

    def get_index_url(self):  # used for pagination links
        return self.get_usage_url(self.object)

    def get_page_subtitle(self):
        return get_latest_str(self.object)

    def get_breadcrumbs_items(self):
        items = []
        if self.index_url_name:
            items.append(
                {
                    "url": reverse(self.index_url_name),
                    "label": capfirst(self.object._meta.verbose_name_plural),
                }
            )
        edit_url = self.get_edit_url(self.object)
        if edit_url:
            items.append(
                {
                    "url": edit_url,
                    "label": get_latest_str(self.object),
                }
            )
        items.append(
            {
                "url": "",
                "label": _("Usage"),
                "sublabel": self.get_page_subtitle(),
            }
        )
        return self.breadcrumbs_items + items

    @cached_property
    def header_buttons(self):
        edit_url = self.get_edit_url(self.object)
        buttons = []
        if edit_url:
            buttons.append(
                HeaderButton(
                    label=_("Edit"),
                    url=edit_url,
                    icon_name="edit",
                )
            )
        return buttons

    def get_queryset(self):
        return ReferenceIndex.get_references_to(self.object).group_by_source_object()

    @cached_property
    def columns(self):
        return [
            TitleColumn(
                "name",
                label=_("Name"),
                accessor="label",
                get_url=lambda r: r["edit_url"],
            ),
            tables.Column(
                "content_type",
                label=_("Type"),
                # Use the content type from the ReferenceIndex object instead of the
                # object itself, so we can get the specific content type without
                # having to fetch the specific object from the database.
                accessor=lambda r: capfirst(r["references"][0].model_name),
            ),
            tables.ReferencesColumn(
                "field",
                label=_("If you confirm deletion")
                if self.describe_on_delete
                else _("Field"),
                accessor="references",
                get_url=lambda r: r["edit_url"],
                describe_on_delete=self.describe_on_delete,
            ),
        ]

    def get_table(self, object_list, **kwargs):
        url_finder = AdminURLFinder(self.request.user)
        results = []
        for object, references in object_list:
            row = {"object": object, "references": references}
            row["edit_url"] = url_finder.get_edit_url(object)
            if row["edit_url"] is None:
                row["label"] = _("(Private %(object)s)") % {
                    "object": object._meta.verbose_name
                }
                row["edit_link_title"] = None
            else:
                row["label"] = str(object)
                row["edit_link_title"] = _("Edit this %(object)s") % {
                    "object": object._meta.verbose_name
                }
            results.append(row)
        return super().get_table(results, **kwargs)

    def get_context_data(self, *args, object_list=None, **kwargs):
        return super().get_context_data(
            *args, object_list=object_list, object=self.object, **kwargs
        )
