from wagtail.documents.views.chooser import viewset as chooser_viewset

DocumentChooserBlock = chooser_viewset.block_class

# When deconstructing a DocumentChooserBlock instance for migrations, the module path
# used in migrations should point to this module
DocumentChooserBlock.__module__ = "wagtail.documents.blocks"
