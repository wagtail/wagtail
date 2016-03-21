from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register)
from .models import Author, Book
from wagtail.tests.testapp.models import EventPage, SingleEventPage

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
    inspect_view_enabled = True
    inspect_view_fields_exclude = ('title', )


class EventPageAdmin(ModelAdmin):
    model = EventPage
    list_display = ('title', 'date_from', 'audience')
    list_filter = ('audience', )
    inspect_view_enabled = True
    inspect_view_fields_exclude = ('feed_image', )


class SingleEventPageAdmin(EventPageAdmin):
    model = SingleEventPage


class EventsAdminGroup(ModelAdminGroup):
    menu_label = "Events"
    items = (EventPageAdmin, SingleEventPageAdmin)
    menu_order = 500


modeladmin_register(AuthorModelAdmin)
modeladmin_register(BookModelAdmin)
modeladmin_register(EventsAdminGroup)
