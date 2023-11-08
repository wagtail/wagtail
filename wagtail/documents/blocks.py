from wagtail.documents.views.chooser import viewset as chooser_viewset

DocumentChooserBlock = chooser_viewset.get_block_class(
    name="DocumentChooserBlock", module_path="wagtail.documents.blocks"
)
