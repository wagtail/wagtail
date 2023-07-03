from wagtail.admin.ui.tables import BaseColumn, Column


class PageTitleColumn(BaseColumn):
    cell_template_name = "wagtailadmin/pages/listing/_page_title_cell.html"

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["page_perms"] = instance.permissions_for_user(
            parent_context["request"].user
        )
        return context


class ParentPageColumn(Column):
    cell_template_name = "wagtailadmin/pages/listing/_parent_page_cell.html"

    def get_value(self, instance):
        return instance.get_parent()


class PageStatusColumn(BaseColumn):
    cell_template_name = "wagtailadmin/pages/listing/_page_status_cell.html"
