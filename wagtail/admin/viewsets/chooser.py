from django.db.models import ForeignKey
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.views.generic import chooser as chooser_views
from wagtail.admin.widgets.chooser import BaseChooser

from .base import ViewSet


class ChooserViewSet(ViewSet):
    icon = "snippet"
    choose_one_text = _("Choose")
    page_title = None
    choose_another_text = _("Choose another")
    edit_item_text = _("Edit")

    choose_view_class = chooser_views.ChooseView
    choose_results_view_class = chooser_views.ChooseResultsView
    chosen_view_class = chooser_views.ChosenView
    base_widget_class = BaseChooser

    register_widget = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.page_title is None:
            self.page_title = self.choose_one_text

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

    @cached_property
    def widget_class(self):
        return type(
            "%sChooserWidget" % self.model.__name__,
            (self.base_widget_class,),
            {
                "model": self.model,
                "choose_one_text": self.choose_one_text,
                "choose_another_text": self.choose_another_text,
                "link_to_chosen_text": self.edit_item_text,
                "chooser_modal_url_name": self.get_url_name("choose"),
                "icon": self.icon,
            },
        )

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("", self.choose_view, name="choose"),
            path("results/", self.choose_results_view, name="choose_results"),
            path("chosen/<str:pk>/", self.chosen_view, name="chosen"),
        ]

    def on_register(self):
        if self.register_widget:
            register_form_field_override(
                ForeignKey, to=self.model, override={"widget": self.widget_class}
            )
