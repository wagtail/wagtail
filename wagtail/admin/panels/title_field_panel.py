from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from wagtail.models import Page

from .field_panel import FieldPanel


class TitleFieldPanel(FieldPanel):
    """
    Prepares the default widget attributes that are used on Page title fields.
    Can be used outside of pages to easily enable the slug field sync functionality.

    :param apply_if_live: (optional) If ``True``, the built in slug sync behaviour will apply irrespective of the published state.
        The default is ``False``, where the slug sync will only apply when the instance is not live (or does not have a live property).
    :param classname: (optional) A CSS class name to add to the panel's HTML element. Default is ``"title"``.
    :param placeholder: (optional) If a value is provided, it will be used as the field's placeholder, if ``False`` is provided no placeholder will be shown.
        If ``True``, a placeholder value of ``"Title*"`` will be used or ``"Page Title*"`` if the model is a ``Page`` model.
        The default is ``True``. If a widget is provided with a placeholder, the widget's value will be used instead.
    :param targets: (optional) This allows you to override the default target of the field named `slug` on the form.
        Accepts a list of field names, default is ``["slug"]``.
        Note that the slugify/urlify behaviour relies on usage of the ``wagtail.admin.widgets.slug`` widget on the slug field.
    """

    def __init__(
        self,
        *args,
        apply_if_live=False,
        classname="title",
        placeholder=True,
        targets=["slug"],
        **kwargs,
    ):
        kwargs["classname"] = classname
        self.apply_if_live = apply_if_live
        self.placeholder = placeholder
        self.targets = targets
        super().__init__(*args, **kwargs)

    def clone_kwargs(self):
        return {
            **super().clone_kwargs(),
            "apply_if_live": self.apply_if_live,
            "placeholder": self.placeholder,
            "targets": self.targets,
        }

    class BoundPanel(FieldPanel.BoundPanel):
        apply_actions = [
            "focus->w-sync#check",
            "blur->w-sync#apply",
            "change->w-sync#apply",
            "keyup->w-sync#apply",
        ]

        def get_editable_context_data(self):
            self.bound_field.field.widget.attrs.update(**self.get_attrs())
            return super().get_editable_context_data()

        def get_attrs(self):
            """
            Generates a dict of widget attributes to be updated on the widget
            before rendering.
            """

            panel = self.panel
            widget = self.bound_field.field.widget

            attrs = {}

            controllers = [widget.attrs.get("data-controller", None), "w-sync"]
            attrs["data-controller"] = " ".join(filter(None, controllers))

            if self.get_should_apply():
                actions = [widget.attrs.get("data-action", None)] + self.apply_actions
                attrs["data-action"] = " ".join(filter(None, actions))

            targets = [
                self.get_target_selector(target)
                for target in panel.targets
                if target in self.form.fields
            ]
            attrs["data-w-sync-target-value"] = ", ".join(filter(None, targets))

            placeholder = self.get_placeholder()
            if placeholder and "placeholder" not in widget.attrs:
                attrs["placeholder"] = placeholder

            return attrs

        def get_placeholder(self):
            """
            If placeholder is falsey, return None. Otherwise allow a valid placeholder
            to be resolved.
            """
            placeholder = self.panel.placeholder

            if not placeholder:
                return None

            if placeholder is True:
                title = gettext_lazy("Title")

                if issubclass(self.panel.model, Page):
                    title = gettext_lazy("Page title")

                return format_lazy("{title}*", title=title)

            return placeholder

        def get_should_apply(self):
            """
            Check that the title field should apply the sync with the target fields.
            """
            if self.panel.apply_if_live:
                return True

            instance = self.instance
            if not instance:
                return True

            is_live = instance.pk and getattr(instance, "live", False)
            return not is_live

        def get_target_selector(self, target):
            """
            Prepare a selector for an individual target field.
            """
            field = self.form[target]
            return f"#{field.id_for_label}"
