from __future__ import absolute_import, unicode_literals

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.contrib.modeladmin.views import CreateView
from wagtail.tests.testapp.models import BusinessChild, EventPage, SingleEventPage

from .forms import PublisherModelAdminForm
from .models import Author, Book, Publisher, Token, VenuePage


class AuthorModelAdmin(ModelAdmin):
    model = Author
    menu_order = 200
    list_display = ('name', 'date_of_birth')
    list_filter = ('date_of_birth', )
    search_fields = ('name', )
    inspect_view_enabled = True
    inspect_view_fields = ('name', )


class BookModelAdmin(ModelAdmin):
    model = Book
    menu_order = 300
    list_display = ('title', 'author')
    list_filter = ('author', )
    ordering = ('title', )
    search_fields = ('title', )
    inspect_view_enabled = True
    inspect_view_fields_exclude = ('title', )

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
