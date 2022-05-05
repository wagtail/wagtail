from django.urls import path
from django.utils.translation import gettext as _

from wagtail.admin.views.generic import chooser as chooser_views

from .base import ViewSet


class ChooserViewSet(ViewSet):
    icon = "snippet"
    page_title = _("Choose")

    choose_view_class = chooser_views.ChooseView
    choose_results_view_class = chooser_views.ChooseResultsView
    chosen_view_class = chooser_views.ChosenView

    @property
    def choose_view(self):
        return self.choose_view_class.as_view(
            model=self.model,
            chosen_url_name=self.get_url_name("chosen"),
            results_url_name=self.get_url_name("choose_results"),
            icon=self.icon,
            page_title=self.page_title,
        )

    @property
    def choose_results_view(self):
        return self.choose_results_view_class.as_view(
            model=self.model,
            chosen_url_name=self.get_url_name("chosen"),
            results_url_name=self.get_url_name("choose_results"),
        )

    @property
    def chosen_view(self):
        return self.chosen_view_class.as_view(
            model=self.model,
        )

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("", self.choose_view, name="choose"),
            path("results/", self.choose_results_view, name="choose_results"),
            path("chosen/<str:pk>/", self.chosen_view, name="chosen"),
        ]
