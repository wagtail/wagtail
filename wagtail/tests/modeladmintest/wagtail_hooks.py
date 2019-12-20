from wagtail.admin.edit_handlers import FieldPanel, ObjectList, TabbedInterface
from wagtail.contrib.modeladmin.helpers import WagtailBackendSearchHandler
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, ThumbnailMixin, modeladmin_register)
from wagtail.contrib.modeladmin.views import CreateView
from wagtail.tests.testapp.models import BusinessChild, EventPage, SingleEventPage

from .forms import PublisherModelAdminForm
from .models import Author, Book, Contributor, Friend, Person, Publisher, Token, VenuePage, Visitor


class AuthorModelAdmin(ModelAdmin):
    model = Author
    menu_order = 200
    list_display = ('name', 'first_book', 'last_book', 'date_of_birth')
    list_filter = ('date_of_birth', )
    search_fields = ('name', )
    inspect_view_enabled = True
    inspect_view_fields = ('name', 'author_birth_string')

    def last_book(self, obj):
        # For testing use of modeladmin methods in list_display
        book = obj.book_set.last()
        if book:
            return book.title
        return ''

    def get_extra_class_names_for_field_col(self, obj, field_name):
        class_names = super(
            AuthorModelAdmin, self
        ).get_extra_class_names_for_field_col(field_name, obj)
        if field_name == 'first_book':
            class_names.append('for-author-%s' % obj.pk)
        return class_names

    def get_extra_attrs_for_field_col(self, obj, field_name):
        attrs = super().get_extra_attrs_for_field_col(
            field_name, obj
        )
        if field_name == 'last_book':
            attrs['data-for_author'] = obj.id
        return attrs


class BookModelAdmin(ThumbnailMixin, ModelAdmin):
    model = Book
    menu_order = 300
    list_display = ('title', 'author', 'admin_thumb')
    list_filter = ('author', )
    ordering = ('title', )
    inspect_view_enabled = True
    inspect_view_fields_exclude = ('title', )
    thumb_image_field_name = 'cover_image'
    search_handler_class = WagtailBackendSearchHandler

    def get_extra_attrs_for_row(self, obj, context):
        return {
            'data-author-yob': obj.author.date_of_birth.year,
            'class': 'book',
        }


class TokenModelAdmin(ModelAdmin):
    model = Token
    list_display = ('key',)


class PublisherCreateView(CreateView):
    def get_form_class(self):
        return PublisherModelAdminForm


class PublisherModelAdmin(ModelAdmin):
    model = Publisher
    create_view_class = PublisherCreateView


class EventPageAdmin(ModelAdmin):
    model = EventPage
    list_display = ('title', 'date_from', 'audience')
    list_filter = ('audience', )
    search_fields = ('title', )
    inspect_view_enabled = True
    inspect_view_fields_exclude = ('feed_image', )


class SingleEventPageAdmin(EventPageAdmin):
    model = SingleEventPage


class VenuePageAdmin(ModelAdmin):
    model = VenuePage
    exclude_from_explorer = True


class PersonAdmin(ModelAdmin):
    model = Person


class FriendAdmin(ModelAdmin):
    model = Friend


class VisitorAdmin(ModelAdmin):
    model = Visitor

    panels = [
        FieldPanel('last_name'),
        FieldPanel('phone_number'),
        FieldPanel('address'),
    ]
    edit_handler = TabbedInterface([
        ObjectList(panels),
    ])


class ContributorAdmin(ModelAdmin):
    model = Contributor

    panels = [
        FieldPanel('last_name'),
        FieldPanel('phone_number'),
        FieldPanel('address'),
    ]


class EventsAdminGroup(ModelAdminGroup):
    menu_label = "Events"
    items = (EventPageAdmin, SingleEventPageAdmin, VenuePageAdmin)
    menu_order = 500


class BusinessChildAdmin(ModelAdmin):
    model = BusinessChild
    # having "Business Child" permanently in the menu confuses tests for the 'add page' view
    menu_label = "BusinessSprog"


modeladmin_register(AuthorModelAdmin)
modeladmin_register(BookModelAdmin)
modeladmin_register(TokenModelAdmin)
modeladmin_register(PublisherModelAdmin)
modeladmin_register(EventsAdminGroup)
modeladmin_register(BusinessChildAdmin)
modeladmin_register(PersonAdmin)
modeladmin_register(FriendAdmin)
modeladmin_register(VisitorAdmin)
modeladmin_register(ContributorAdmin)
