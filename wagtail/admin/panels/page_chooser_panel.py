from wagtail.admin.widgets import AdminPageChooser

from .field_panel import FieldPanel


class PageChooserPanel(FieldPanel):
    def __init__(self, field_name, page_type=None, can_choose_root=False):
        super().__init__(field_name=field_name)

        self.page_type = page_type
        self.can_choose_root = can_choose_root

    def clone_kwargs(self):
        return {
            "field_name": self.field_name,
            "page_type": self.page_type,
            "can_choose_root": self.can_choose_root,
        }

    def get_form_options(self):
        opts = super().get_form_options()

        if self.page_type or self.can_choose_root:
            widgets = opts.setdefault("widgets", {})
            widgets[self.field_name] = AdminPageChooser(
                target_models=self.page_type, can_choose_root=self.can_choose_root
            )

        return opts
