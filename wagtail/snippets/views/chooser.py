from django.db.models import ForeignKey
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.ui.tables import LiveStatusTagColumn
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenMultipleView,
    ChosenView,
    CreateView,
    CreationFormMixin,
)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.models import DraftStateMixin
from wagtail.snippets.widgets import AdminSnippetChooser
from wagtail.telepath import register as register_telepath_adapter


class BaseSnippetChooseView(BaseChooseView):
    filter_form_class = None
    page_title = _("Choose")
    results_template_name = "wagtailsnippets/chooser/results.html"
    per_page = 25

    @property
    def page_subtitle(self):
        return self.model._meta.verbose_name

    @property
    def columns(self):
        columns = super().columns
        if issubclass(self.model, DraftStateMixin):
            columns += [LiveStatusTagColumn(sort_key=None)]
        return columns

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "snippet_type_name": self.model._meta.verbose_name,
                "add_url_name": self.model.snippet_viewset.get_url_name("add"),
            }
        )
        return context


class ChooseView(ChooseViewMixin, CreationFormMixin, BaseSnippetChooseView):
    pass


class ChooseResultsView(
    ChooseResultsViewMixin, CreationFormMixin, BaseSnippetChooseView
):
    pass


class SnippetChosenView(ChosenView):
    response_data_title_key = "string"


class SnippetChosenMultipleView(ChosenMultipleView):
    response_data_title_key = "string"


class SnippetCreateView(CreateView):
    response_data_title_key = "string"


class SnippetChooserViewSet(ChooserViewSet):
    choose_view_class = ChooseView
    choose_results_view_class = ChooseResultsView
    chosen_view_class = SnippetChosenView
    chosen_multiple_view_class = SnippetChosenMultipleView
    create_view_class = SnippetCreateView
    base_widget_class = AdminSnippetChooser

    @cached_property
    def widget_class(self):
        """
        Returns the form widget class for this chooser.
        """
        widget_class_name = f"{self.model_name}ChooserWidget"

        return type(
            widget_class_name,
            (self.base_widget_class,),
            {
                "model": self.model,
                "icon": self.icon,
            },
        )

    def on_register(self):
        if self.model and self.register_widget:
            register_form_field_override(
                ForeignKey,
                to=self.model,
                override=lambda db_field: {
                    "widget": self.widget_class(
                        model=self.model,
                        to_field_name=getattr(
                            db_field.remote_field, "field_name", None
                        ),
                    )
                },
            )
            if self.widget_telepath_adapter_class:
                adapter = self.widget_telepath_adapter_class()
                register_telepath_adapter(adapter, self.widget_class)
