from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.tables import LiveStatusTagColumn
from wagtail.admin.views.generic.chooser import (
    BaseChooseView,
    ChooseResultsViewMixin,
    ChooseViewMixin,
    ChosenMultipleView,
    ChosenView,
    CreationFormMixin,
)
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.models import DraftStateMixin


class BaseSnippetChooseView(BaseChooseView):
    filter_form_class = None
    icon = "snippet"
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

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        context.update(
            {
                "snippet_type_name": self.model._meta.verbose_name,
                "add_url_name": f"wagtailsnippets_{app_label}_{model_name}:add",
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


class SnippetChooserViewSet(ChooserViewSet):
    register_widget = False  # registering the snippet chooser widget for a given model is done in register_snippet
    choose_view_class = ChooseView
    choose_results_view_class = ChooseResultsView
    chosen_view_class = SnippetChosenView
    chosen_multiple_view_class = SnippetChosenMultipleView
