from django.forms import Media
from django.utils.functional import cached_property

from .base import Panel


class PanelGroup(Panel):
    """
    Abstract class for panels that manage a set of sub-panels.
    Concrete subclasses must attach a 'children' property
    """

    def __init__(self, children=(), *args, **kwargs):
        permission = kwargs.pop("permission", None)
        super().__init__(*args, **kwargs)
        self.children = children
        self.permission = permission

    def clone_kwargs(self):
        kwargs = super().clone_kwargs()
        kwargs["children"] = self.children
        kwargs["permission"] = self.permission
        return kwargs

    def get_form_options(self):
        if self.model is None:
            raise AttributeError(
                "%s is not bound to a model yet. Use `.bind_to_model(model)` "
                "before using this method." % self.__class__.__name__
            )

        options = {}

        # Merge in form options from each child in turn, combining values that are types that we
        # know how to combine (i.e. lists, dicts and sets)
        for child in self.children:
            child_options = child.get_form_options()
            for key, new_val in child_options.items():
                if key not in options:
                    # if val is a known mutable container type that we're going to merge subsequent
                    # child values into, create a copy so that we don't risk that change leaking
                    # back into the child's internal state
                    if (
                        isinstance(new_val, list)
                        or isinstance(new_val, dict)
                        or isinstance(new_val, set)
                    ):
                        options[key] = new_val.copy()
                    else:
                        options[key] = new_val
                else:
                    current_val = options[key]
                    if isinstance(current_val, list) and isinstance(
                        new_val, (list, tuple)
                    ):
                        current_val.extend(new_val)
                    elif isinstance(current_val, tuple) and isinstance(
                        new_val, (list, tuple)
                    ):
                        options[key] = list(current_val).extend(new_val)
                    elif isinstance(current_val, dict) and isinstance(new_val, dict):
                        current_val.update(new_val)
                    elif isinstance(current_val, set) and isinstance(new_val, set):
                        current_val.update(new_val)
                    else:
                        raise ValueError(
                            "Don't know how to merge values %r and %r for form option %r"
                            % (current_val, new_val, key)
                        )

        return options

    def on_model_bound(self):
        from .model_utils import expand_panel_list

        child_panels = expand_panel_list(self.model, self.children)
        self.children = [child.bind_to_model(self.model) for child in child_panels]

    @cached_property
    def child_identifiers(self):
        """
        A list of identifiers corresponding to child panels in ``self.children``, formed from the clean_name property
        but validated to be unique and non-empty.
        """
        used_names = set()
        result = []
        for panel in self.children:
            base_name = panel.clean_name or "panel"
            candidate_name = base_name
            suffix = 0
            while candidate_name in used_names:
                suffix += 1
                candidate_name = "%s%d" % (base_name, suffix)

            result.append(candidate_name)
            used_names.add(candidate_name)

        return result

    class BoundPanel(Panel.BoundPanel):
        @cached_property
        def children(self):
            return [
                child.get_bound_panel(
                    instance=self.instance,
                    request=self.request,
                    form=self.form,
                    prefix=(f"{self.prefix}-child-{identifier}"),
                )
                for child, identifier in zip(
                    self.panel.children, self.panel.child_identifiers
                )
            ]

        @cached_property
        def visible_children(self):
            return [child for child in self.children if child.is_shown()]

        @cached_property
        def visible_children_with_identifiers(self):
            return [
                (child, identifier)
                for child, identifier in zip(
                    self.children, self.panel.child_identifiers
                )
                if child.is_shown()
            ]

        def show_panel_furniture(self):
            return any(child.show_panel_furniture() for child in self.children)

        def is_shown(self):
            """
            Check permissions on the panel group overall then check if any children
            are shown.
            """

            if self.panel.permission:
                if not self.request.user.has_perm(self.panel.permission):
                    return False

            return any(child.is_shown() for child in self.children)

        @property
        def media(self):
            media = Media()
            for item in self.visible_children:
                media += item.media
            return media

        def get_comparison(self):
            comparators = []

            for child in self.children:
                comparators.extend(child.get_comparison())

            return comparators


class TabbedInterface(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/tabbed_interface.html"


class ObjectList(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/object_list.html"


class FieldRowPanel(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/field_row_panel.html"


class MultiFieldPanel(PanelGroup):
    class BoundPanel(PanelGroup.BoundPanel):
        template_name = "wagtailadmin/panels/multi_field_panel.html"
