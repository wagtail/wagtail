from django.db.models import ForeignKey
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.views.generic import chooser as chooser_views
from wagtail.admin.widgets.chooser import BaseChooser
from wagtail.blocks import ChooserBlock
from wagtail.telepath import register as register_telepath_adapter

from .base import ViewSet


class ChooserViewSet(ViewSet):
    """
    A viewset that creates a chooser modal interface for choosing model instances.
    """

    model = None

    icon = "snippet"  #: The icon to use in the header of the chooser modal, and on the chooser widget
    choose_one_text = _(
        "Choose"
    )  #: Label for the 'choose' button in the chooser widget when choosing an initial item
    page_title = None  #: Title text for the chooser modal (defaults to the same as ``choose_one_text``)`
    choose_another_text = _(
        "Choose another"
    )  #: Label for the 'choose' button in the chooser widget, when an item has already been chosen
    edit_item_text = _("Edit")  #: Label for the 'edit' button in the chooser widget

    per_page = 10  #: Number of results to show per page

    #: A list of URL query parameters that should be passed on unmodified as part of any links or
    #: form submissions within the chooser modal workflow.
    preserve_url_parameters = ["multiple"]

    #: The view class to use for the overall chooser modal; must be a subclass of ``wagtail.admin.views.generic.chooser.ChooseView``.
    choose_view_class = chooser_views.ChooseView

    #: The view class used to render just the results panel within the chooser modal; must be a subclass of ``wagtail.admin.views.generic.chooser.ChooseResultsView``.
    choose_results_view_class = chooser_views.ChooseResultsView

    #: The view class used after an item has been chosen; must be a subclass of ``wagtail.admin.views.generic.chooser.ChosenView``.
    chosen_view_class = chooser_views.ChosenView

    #: The view class used after multiple items have been chosen; must be a subclass of ``wagtail.admin.views.generic.chooser.ChosenMultipleView``.
    chosen_multiple_view_class = chooser_views.ChosenMultipleView

    #: The view class used to handle submissions of the 'create' form; must be a subclass of ``wagtail.admin.views.generic.chooser.CreateView``.
    create_view_class = chooser_views.CreateView

    #: The base Widget class that the chooser widget will be derived from.
    base_widget_class = BaseChooser

    #: The adapter class used to map the widget class to its JavaScript implementation - see :ref:`streamfield_widget_api`.
    #: Only required if the chooser uses custom JavaScript code.
    widget_telepath_adapter_class = None

    #: The base ChooserBlock class that the StreamField chooser block will be derived from.
    base_block_class = ChooserBlock

    #: Defaults to True; if False, the chooser widget will not automatically be registered for use in admin forms.
    register_widget = True

    #: Form class to use for the form in the "Create" tab of the modal.
    creation_form_class = None

    #: List of model fields that should be included in the creation form, if creation_form_class is not specified.
    form_fields = None

    #: List of model fields that should be excluded from the creation form, if creation_form_class.
    #: If none of ``creation_form_class``, ``form_fields`` or ``exclude_form_fields`` are specified, the "Create" tab will be omitted.
    exclude_form_fields = None

    search_tab_label = _("Search")  #: Label for the 'search' tab in the chooser modal
    create_action_label = _(
        "Create"
    )  #: Label for the submit button on the 'create' form
    create_action_clicked_label = None  #: Alternative text to display on the submit button after it has been clicked
    creation_tab_label = None  #: Label for the 'create' tab in the chooser modal (defaults to the same as create_action_label)

    permission_policy = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.page_title is None:
            self.page_title = self.choose_one_text

    @property
    def choose_view(self):
        return self.choose_view_class.as_view(
            model=self.model,
            chosen_url_name=self.get_url_name("chosen"),
            chosen_multiple_url_name=self.get_url_name("chosen_multiple"),
            results_url_name=self.get_url_name("choose_results"),
            create_url_name=self.get_url_name("create"),
            icon=self.icon,
            page_title=self.page_title,
            per_page=self.per_page,
            creation_form_class=self.creation_form_class,
            form_fields=self.form_fields,
            exclude_form_fields=self.exclude_form_fields,
            search_tab_label=self.search_tab_label,
            creation_tab_label=self.creation_tab_label,
            create_action_label=self.create_action_label,
            create_action_clicked_label=self.create_action_clicked_label,
            permission_policy=self.permission_policy,
            preserve_url_parameters=self.preserve_url_parameters,
        )

    @property
    def choose_results_view(self):
        return self.choose_results_view_class.as_view(
            model=self.model,
            chosen_url_name=self.get_url_name("chosen"),
            chosen_multiple_url_name=self.get_url_name("chosen_multiple"),
            results_url_name=self.get_url_name("choose_results"),
            per_page=self.per_page,
            creation_form_class=self.creation_form_class,
            form_fields=self.form_fields,
            exclude_form_fields=self.exclude_form_fields,
            create_action_label=self.create_action_label,
            create_action_clicked_label=self.create_action_clicked_label,
            permission_policy=self.permission_policy,
            preserve_url_parameters=self.preserve_url_parameters,
        )

    @property
    def chosen_view(self):
        return self.chosen_view_class.as_view(
            model=self.model,
        )

    @property
    def chosen_multiple_view(self):
        return self.chosen_multiple_view_class.as_view(
            model=self.model,
        )

    @property
    def create_view(self):
        return self.create_view_class.as_view(
            model=self.model,
            create_url_name=self.get_url_name("create"),
            creation_form_class=self.creation_form_class,
            form_fields=self.form_fields,
            exclude_form_fields=self.exclude_form_fields,
            create_action_label=self.create_action_label,
            create_action_clicked_label=self.create_action_clicked_label,
            permission_policy=self.permission_policy,
            preserve_url_parameters=self.preserve_url_parameters,
        )

    @cached_property
    def model_name(self):
        if isinstance(self.model, str):
            return self.model.split(".")[-1]
        else:
            return self.model.__name__

    @cached_property
    def widget_class(self):
        """
        Returns the form widget class for this chooser.
        """
        if self.model is None:
            widget_class_name = "ChooserWidget"
        else:
            if isinstance(self.model, str):
                model_name = self.model.split(".")[-1]
            else:
                model_name = self.model.__name__
            widget_class_name = "%sChooserWidget" % model_name

        return type(
            widget_class_name,
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

    def get_block_class(self, name=None, module_path=None):
        """
        Returns a StreamField ChooserBlock class using this chooser.

        :param name: Name to give to the class; defaults to the model name with "ChooserBlock" appended
        :param module_path: The dotted path of the module where the class can be imported from; used when
            deconstructing the block definition for migration files.
        """
        meta = type(
            "Meta",
            (self.base_block_class._meta_class,),
            {
                "icon": self.icon,
            },
        )
        cls = type(
            name or "%sChooserBlock" % self.model_name,
            (self.base_block_class,),
            {
                "target_model": self.model,
                "widget": self.widget_class(),
                "Meta": meta,
            },
        )
        if module_path:
            cls.__module__ = module_path
        return cls

    def get_urlpatterns(self):
        return super().get_urlpatterns() + [
            path("", self.choose_view, name="choose"),
            path("results/", self.choose_results_view, name="choose_results"),
            path("chosen/<str:pk>/", self.chosen_view, name="chosen"),
            path("chosen-multiple/", self.chosen_multiple_view, name="chosen_multiple"),
            path("create/", self.create_view, name="create"),
        ]

    def on_register(self):
        if self.model and self.register_widget:
            register_form_field_override(
                ForeignKey, to=self.model, override={"widget": self.widget_class}
            )
            if self.widget_telepath_adapter_class:
                adapter = self.widget_telepath_adapter_class()
                register_telepath_adapter(adapter, self.widget_class)
