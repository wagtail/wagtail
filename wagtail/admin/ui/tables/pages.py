from django.utils.safestring import mark_safe
from django.utils.translation import gettext

from wagtail.admin.ui.tables import BaseColumn, BulkActionsCheckboxColumn, Column, Table


class PageTitleColumn(BaseColumn):
    header_template_name = "wagtailadmin/pages/listing/_page_title_column_header.html"
    cell_template_name = "wagtailadmin/pages/listing/_page_title_cell.html"
    classname = "title"

    def get_header_context_data(self, parent_context):
        context = super().get_header_context_data(parent_context)
        context["page_obj"] = parent_context.get("page_obj")
        context["parent_page"] = parent_context.get("parent_page")
        context["is_searching"] = parent_context.get("is_searching")
        context["is_searching_whole_tree"] = parent_context.get(
            "is_searching_whole_tree"
        )
        return context

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["page_perms"] = instance.permissions_for_user(
            parent_context["request"].user
        )
        context["parent_page"] = getattr(instance, "annotated_parent_page", None)
        context["show_locale_labels"] = parent_context.get("show_locale_labels")
        context["perms"] = parent_context.get("perms")
        context["actions_next_url"] = parent_context.get("actions_next_url")
        return context


class ParentPageColumn(Column):
    cell_template_name = "wagtailadmin/pages/listing/_parent_page_cell.html"

    def get_value(self, instance):
        return instance.get_parent()


class PageStatusColumn(BaseColumn):
    cell_template_name = "wagtailadmin/pages/listing/_page_status_cell.html"


class BulkActionsColumn(BulkActionsCheckboxColumn):
    def get_header_context_data(self, parent_context):
        context = super().get_header_context_data(parent_context)
        parent_page = parent_context.get("parent_page")
        if parent_page:
            context["parent"] = parent_page.id
        return context

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context.update(
            {
                "obj_type": "page",
                "aria_labelledby_prefix": "page_",
                "aria_labelledby": str(instance.pk),
                "aria_labelledby_suffix": "_title",
                "checkbox_aria_label": gettext("Select page"),
            }
        )
        return context


class OrderingColumn(BaseColumn):
    header_template_name = "wagtailadmin/pages/listing/_ordering_header.html"
    cell_template_name = "wagtailadmin/pages/listing/_ordering_cell.html"


class NavigateToChildrenColumn(BaseColumn):
    cell_template_name = "wagtailadmin/pages/listing/_navigation_explore.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["page"] = instance
        context["page_perms"] = instance.permissions_for_user(
            parent_context["request"].user
        )
        return context

    def render_header_html(self, parent_context):
        return mark_safe("<th></th>")


class PageTable(Table):
    def __init__(
        self,
        *args,
        use_row_ordering_attributes=False,
        parent_page=None,
        show_locale_labels=False,
        actions_next_url=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # If true, attributes will be added on the <tr> element to support reordering
        self.use_row_ordering_attributes = use_row_ordering_attributes

        # The parent page of the pages being listed - used to add extra context to the title text
        # of the reordering links. Leave this undefined if the pages being listed do not share a
        # common parent.
        self.parent_page = parent_page
        if self.parent_page:
            # Use more detailed title text that mentions the parent page, if we have one and the
            # current strings have not been overridden from Table's default
            if self.ascending_title_text_format == Table.ascending_title_text_format:
                self.ascending_title_text_format = gettext(
                    "Sort the order of child pages within '%(parent)s' by '%(label)s' in ascending order."
                )
            if self.descending_title_text_format == Table.descending_title_text_format:
                self.descending_title_text_format = gettext(
                    "Sort the order of child pages within '%(parent)s' by '%(label)s' in descending order."
                )

        self.show_locale_labels = show_locale_labels
        self.actions_next_url = actions_next_url

    def get_ascending_title_text(self, column):
        return self.ascending_title_text_format % {
            "parent": self.parent_page and self.parent_page.get_admin_display_title(),
            "label": column.label,
        }

    def get_descending_title_text(self, column):
        return self.descending_title_text_format % {
            "parent": self.parent_page and self.parent_page.get_admin_display_title(),
            "label": column.label,
        }

    def get_row_classname(self, instance):
        if not instance.live:
            return "unpublished"
        else:
            return ""

    def get_row_attrs(self, instance):
        attrs = super().get_row_attrs(instance)
        if self.use_row_ordering_attributes:
            attrs["id"] = "page_%d" % instance.id
            attrs["data-page-title"] = instance.get_admin_display_title()
        return attrs

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["show_locale_labels"] = self.show_locale_labels
        context["perms"] = parent_context.get("perms")
        context["page_obj"] = parent_context.get("page_obj")
        context["parent_page"] = parent_context.get("parent_page")
        context["is_searching"] = parent_context.get("is_searching")
        context["is_searching_whole_tree"] = parent_context.get(
            "is_searching_whole_tree"
        )
        context["actions_next_url"] = (
            self.actions_next_url or parent_context.get("request").path
        )
        return context
