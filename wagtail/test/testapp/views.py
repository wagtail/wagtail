import calendar

from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test
from wagtail.admin.filters import WagtailFilterSet
from wagtail.admin.panels import FieldPanel
from wagtail.admin.ui.tables import BooleanColumn, Column, UpdatedAtColumn
from wagtail.admin.views.generic import DeleteView, EditView, IndexView
from wagtail.admin.viewsets.base import ViewSet, ViewSetGroup
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.viewsets.model import ModelViewSet, ModelViewSetGroup
from wagtail.admin.viewsets.pages import PageListingViewSet
from wagtail.contrib.forms.views import SubmissionsListView
from wagtail.test.testapp.models import (
    Advert,
    EventPage,
    FeatureCompleteToy,
    JSONBlockCountsStreamModel,
    JSONMinMaxCountStreamModel,
    JSONStreamModel,
    ModelWithStringTypePrimaryKey,
    SearchTestModel,
)


def user_is_called_bob(user):
    return user.first_name == "Bob"


@user_passes_test(user_is_called_bob)
def bob_only_zone(request):
    return HttpResponse("Bobs of the world unite!")


def message_test(request):
    if request.method == "POST":
        fn = getattr(messages, request.POST["level"])
        fn(request, request.POST["message"])
        return redirect("testapp_message_test")
    else:
        return TemplateResponse(request, "wagtailadmin/base.html")


class CustomSubmissionsListView(SubmissionsListView):
    paginate_by = 50
    default_ordering = ("submit_time",)
    ordering_csv = ("-submit_time",)

    def get_csv_filename(self):
        """Returns the filename for CSV file with page title at start"""
        filename = super().get_csv_filename()
        return self.form_page.slug + "-" + filename


class TestIndexView(IndexView):
    model = ModelWithStringTypePrimaryKey
    index_url_name = "testapp_generic_index"
    template_name = "tests/generic_view_templates/index.html"
    paginate_by = 20
    context_object_name = "test_object"


class TestIndexViewWithoutModel(IndexView):
    def get_base_queryset(self):
        return ModelWithStringTypePrimaryKey.objects.all()


class CustomModelEditForm(forms.ModelForm):
    class Meta:
        model = ModelWithStringTypePrimaryKey
        fields = ("content",)


class TestEditView(EditView):
    model = ModelWithStringTypePrimaryKey
    context_object_name = "test_object"
    template_name = "tests/generic_view_templates/edit.html"
    index_url_name = "testapp_generic_index"
    success_url = "testapp_generic_index"
    edit_url_name = "testapp_generic_edit"
    delete_url_name = "testapp_generic_delete"
    form_class = CustomModelEditForm
    success_message = gettext_lazy("User '%(object)s' updated.")
    page_title = gettext_lazy("test edit view")


class TestDeleteView(DeleteView):
    model = ModelWithStringTypePrimaryKey
    context_object_name = "test_object"
    template_name = "tests/generic_view_templates/delete.html"
    index_url_name = "testapp_generic_index"
    edit_url_name = "testapp_generic_edit"
    delete_url_name = "testapp_generic_delete"
    success_message = gettext_lazy("User '%(object)s' updated.")
    page_title = gettext_lazy("test delete view")


class CalendarViewSet(ViewSet):
    menu_label = "The Calendar"
    icon = "date"
    name = "calendar"
    template_name = "tests/misc/calendar.html"

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.now = timezone.now()

    def index(self, request):
        calendar_html = calendar.HTMLCalendar().formatyear(self.now.year)
        return render(
            request,
            self.template_name,
            {
                "calendar_html": calendar_html,
                "page_title": f"{self.now.year} calendar",
                "header_icon": self.icon,
            },
        )

    def month(self, request):
        calendar_html = calendar.HTMLCalendar().formatmonth(
            self.now.year, self.now.month
        )
        return render(
            request,
            self.template_name,
            {
                "calendar_html": calendar_html,
                "page_title": f"{self.now.year}/{self.now.month} calendar",
                "header_icon": self.icon,
            },
        )

    def get_urlpatterns(self):
        return [
            path("", self.index, name="index"),
            path("month/", self.month, name="month"),
        ]


class GreetingsViewSet(ViewSet):
    menu_label = "The Greetings"
    icon = "user"
    url_namespace = "greetings"
    url_prefix = "greetingz"

    def index(self, request):
        return render(
            request,
            "tests/misc/greetings.html",
            {"page_title": "Greetings", "header_icon": self.icon},
        )

    def get_urlpatterns(self):
        return [
            path("", self.index, name="index"),
        ]


class MiscellaneousViewSetGroup(ViewSetGroup):
    items = (CalendarViewSet, GreetingsViewSet)
    menu_label = "Miscellaneous"


class JSONStreamModelViewSet(ModelViewSet):
    name = "streammodel"
    model = JSONStreamModel
    exclude_form_fields = []
    icon = "rotate"


class JSONMinMaxCountStreamModelViewSet(ModelViewSet):
    url_namespace = "minmaxcount_streammodel"
    url_prefix = "minmaxcount-streammodel"
    model = JSONMinMaxCountStreamModel
    form_fields = ("body",)
    icon = "rotate"
    menu_label = "JSON MinMaxCount StreamModel"


class JSONModelViewSetGroup(ModelViewSetGroup):
    items = (
        JSONStreamModelViewSet,
        JSONMinMaxCountStreamModelViewSet,
        # Can be an instance instead of class
        ModelViewSet(
            model=JSONBlockCountsStreamModel,
            exclude_form_fields=(),
            icon="resubmit",
            url_namespace="blockcounts_streammodel",
            url_prefix="blockcounts/streammodel",
            menu_label="JSON BlockCounts StreamModel",
        ),
    )


class SearchTestModelViewSet(ModelViewSet):
    model = SearchTestModel
    search_fields = ["title", "body"]
    form_fields = ["title", "body"]


class FeatureCompleteToyIndexView(IndexView):
    model = FeatureCompleteToy
    default_ordering = ["name", "-release_date"]


class FeatureCompleteToyViewSet(ModelViewSet):
    model = FeatureCompleteToy
    url_namespace = "feature_complete_toy"
    url_prefix = "feature-complete-toy"
    menu_label = "Feature Complete Toys"
    icon = "media"
    template_prefix = "customprefix/"
    index_template_name = "tests/fctoy_index.html"
    index_view_class = FeatureCompleteToyIndexView
    list_display = ["name", BooleanColumn("is_cool"), UpdatedAtColumn()]
    list_filter = ["name", "release_date"]
    list_export = ["name", "release_date", "is_cool"]
    export_filename = "feature-complete-toys"
    export_headings = {"release_date": "Launch date"}
    list_per_page = 5
    # search_fields derived from the model
    inspect_view_enabled = True
    inspect_view_fields = ["strid", "release_date"]

    panels = [
        FieldPanel("name"),
        FieldPanel("release_date", permission="tests.can_set_release_date"),
    ]


class FCToyAlt1ViewSet(ModelViewSet):
    model = FeatureCompleteToy
    icon = "media"
    list_filter = {"name": ["icontains"]}
    form_fields = ["name"]
    menu_label = "FC Toys Alt 1"
    inspect_view_enabled = True
    inspect_view_fields_exclude = ["strid", "release_date"]
    copy_view_enabled = False

    def get_index_view_kwargs(self, **kwargs):
        return super().get_index_view_kwargs(is_searchable=False, **kwargs)


class FCToyCustomFilterSet(WagtailFilterSet):
    class Meta:
        model = FeatureCompleteToy
        fields = {"release_date": ["year__lte"]}


class ToyViewSetGroup(ModelViewSetGroup):
    menu_label = "Toys"
    menu_icon = "media"

    items = (
        FeatureCompleteToyViewSet,
        FCToyAlt1ViewSet(name="fctoy_alt1"),
        ModelViewSet(
            name="fctoy-alt2",
            menu_label="FC Toys Alt 2",
            model=FeatureCompleteToy,
            icon="media",
            filterset_class=FCToyCustomFilterSet,
            exclude_form_fields=(),
            search_fields=["name"],
            search_backend_name=None,
        ),
        ModelViewSet(
            name="fctoy-alt3",
            menu_label="FC Toys Alt 3",
            model=FeatureCompleteToy,
            exclude_form_fields=(),
            index_view_class=FeatureCompleteToyIndexView,
            list_display=["name", "strid", "release_date"],
            ordering=["strid"],
            copy_view_enabled=False,
        ),
    )


class AnimatedAdvertChooserViewSet(ChooserViewSet):
    model = Advert
    register_widget = False  # don't make this the registered widget for Advert
    url_filter_parameters = ["url"]
    preserve_url_parameters = ["multiple", "url"]

    def get_object_list(self):
        return Advert.objects.filter(tags__name="animated")


animated_advert_chooser_viewset = AnimatedAdvertChooserViewSet(
    "animated_advert_chooser"
)

AdvertChooserWidget = animated_advert_chooser_viewset.widget_class


class EventPageFilterSet(PageListingViewSet.filterset_class):
    class Meta:
        model = EventPage
        fields = ["audience"]


class EventPageListingViewSet(PageListingViewSet):
    model = EventPage
    icon = "calendar"
    menu_label = "Event pages"
    add_to_admin_menu = True
    columns = PageListingViewSet.columns + [
        Column("audience", label="Audience", sort_key="audience"),
    ]
    filterset_class = EventPageFilterSet


event_page_listing_viewset = EventPageListingViewSet("event_pages")
