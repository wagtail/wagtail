from wagtail.admin.ui.fields import BaseFieldDisplay


class DocumentDisplay(BaseFieldDisplay):
    template_name = "wagtaildocs/components/document_display.html"
