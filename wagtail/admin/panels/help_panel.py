from .base import Panel


class HelpPanel(Panel):
    def __init__(
        self,
        content="",
        template="wagtailadmin/panels/help_panel.html",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.content = content
        self.template = template

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        del kwargs["help_text"]
        kwargs.update(
            content=self.content,
            template=self.template,
        )
        return kwargs

    @property
    def clean_name(self):
        return super().clean_name or "help"

    class BoundPanel(Panel.BoundPanel):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.template_name = self.panel.template
            self.content = self.panel.content
