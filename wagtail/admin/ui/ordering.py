from wagtail.admin.ui.tables import BaseColumn


class OrderingColumn(BaseColumn):
    header_template_name = "wagtailadmin/tables/ordering_header.html"
    cell_template_name = "wagtailadmin/tables/ordering_cell.html"
