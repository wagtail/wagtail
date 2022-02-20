from wagtail.admin.edit_handlers import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.modeladmin import register
from wagtail.contrib.modeladmin.helpers import WagtailBackendSearchHandler
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    ThumbnailMixin,
)
from wagtail.contrib.modeladmin.views import CreateView, EditView, IndexView
from wagtail.core.models import Page
from wagtail.tests.testapp.models import BusinessChild, EventPage, SingleEventPage

from .forms import PublisherModelAdminForm
from .models import (
    Author,
    Book,
    Contributor,
    Friend,
    Person,
    Publisher,
    RelatedLink,
    Token,
    VenuePage,
    Visitor,
)


class AuthorModelAdmin(ModelAdmin):
    model = Author
    menu_order = 200
    list_display = ("name", "first_book", "last_book", "date_of_birth")
    list_filter = ("date_of_birth",)
    search_fields = ("name",)
    inspect_view_enabled = True
    inspect_view_fields = ("name", "author_birth_string")

    def last_book(self, obj):
        # For testing use of modeladmin methods in list_display
        book = obj.book_set.last()
        if book:
            return book.title
        return ""

    def get_extra_class_names_for_field_col(self, obj, field_name):
        class_names = super(AuthorModelAdmin, self).get_extra_class_names_for_field_col(
            field_name, obj
        )
        if field_name == "first_book":
            class_names.append("for-author-%s" % obj.pk)
        return class_names

    def get_extra_attrs_for_field_col(self, obj, field_name):
        attrs = super().get_extra_attrs_for_field_col(field_name, obj)
        if field_name == "last_book":
            attrs["data-for_author"] = obj.id
        return attrs


class BookModelIndexView(IndexView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dates before 1900 are not handled by Excel. This works around that
        # by serializing dates in iso format.
        # See: https://bitbucket.org/openpyxl/openpyxl/issues/1325/python-dates-before-march-1-1900-are
        # And:  https://en.wikipedia.org/wiki/Year_1900_problem#Microsoft_Excel
        def date_isoformat(date_obj):
            return date_obj.isoformat()

        self.custom_field_preprocess = {
            "author_date_of_birth": {"xlsx": date_isoformat}
        }


class BookModelAdmin(ThumbnailMixin, ModelAdmin):
    model = Book
    index_view_class = BookModelIndexView
    menu_order = 300
    list_display = ("title", "author", "admin_thumb")
    list_export = ("title", "author", "author_date_of_birth")
    list_filter = ("author",)
    export_filename = "books-export"
    ordering = ("title",)
    inspect_view_enabled = True
    inspect_view_fields_exclude = ("title",)
    thumb_image_field_name = "cover_image"
    search_handler_class = WagtailBackendSearchHandler
    prepopulated_fields = {"title": ("author",)}

    def get_extra_attrs_for_row(self, obj, context):
        return {
            "data-author-yob": obj.author.date_of_birth.year,
            "class": "book",
        }

    def author_date_of_birth(self, obj):
        return obj.author.date_of_birth


class PublisherCreateView(CreateView):
    def get_form_class(self):
        return PublisherModelAdminForm


class PublisherEditView(EditView):
    def get_form_class(self):
        return PublisherModelAdminForm


class PublisherModelAdmin(ModelAdmin):
    model = Publisher
    create_view_class = PublisherCreateView
    edit_view_class = PublisherEditView


register(AuthorModelAdmin)
register(BookModelAdmin)
register(PublisherModelAdmin)


class TokenModelAdmin(ModelAdmin):
    model = Token
    list_display = ("key",)


register(TokenModelAdmin)


class EventPageAdmin(ModelAdmin):
    model = EventPage
    list_display = ("title", "date_from", "audience")
    list_filter = ("audience",)
    search_fields = ("title",)
    inspect_view_enabled = True
    inspect_view_fields_exclude = ("feed_image",)


class SingleEventPageAdmin(EventPageAdmin):
    model = SingleEventPage


class VenuePageAdmin(ModelAdmin):
    model = VenuePage
    exclude_from_explorer = True


class EventsAdminGroup(ModelAdminGroup):
    menu_label = "Events"
    items = (EventPageAdmin, SingleEventPageAdmin, VenuePageAdmin)
    menu_order = 500


register(EventsAdminGroup)


# Register simple modeladmin classes
# ----------------------------------


class PersonAdmin(ModelAdmin):
    model = Person


class VisitorAdmin(ModelAdmin):
    model = Visitor

    panels = [
        FieldPanel("last_name"),
        FieldPanel("phone_number"),
        FieldPanel("address"),
    ]
    edit_handler = TabbedInterface(
        [
            ObjectList(panels),
        ]
    )


# No attribute overrides
register(PersonAdmin)

# Override 'list_display' for this one
register(VisitorAdmin, list_display=["first_name", "last_name", "phone_number"])


# Register model classes directly
# -------------------------------

# No attribute overrides
register(Page)

# Override 'list_display' for this one
register(RelatedLink, list_display=["title", "link"])

# Override menu_label, as having "Business Child" permanently in the menu
# confuses tests for the 'add page' view
register(BusinessChild, menu_label="BusinessSprog")


# Register a model class with an admin class
# ------------------------------------------


class GenericPersonAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "phone_number"]
    panels = [
        FieldPanel("last_name"),
        FieldPanel("phone_number"),
        FieldPanel("address"),
    ]


# Register `Friend` with this class
register(Friend, admin_class=GenericPersonAdmin)

# Register `Contributor` for this class, with overrides
register(Contributor, admin_class=GenericPersonAdmin, list_display=["phone_number"])
