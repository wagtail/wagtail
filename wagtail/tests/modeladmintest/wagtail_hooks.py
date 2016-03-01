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


class BookModelAdmin(ModelAdmin):
    model = Book
    menu_order = 300
    list_display = ('title', 'author')
    list_filter = ('author', )


class EventPageAdmin(ModelAdmin):
    model = EventPage
    list_display = ('title', 'date_from', 'audience')


class SingleEventPageAdmin(EventPageAdmin):
    model = SingleEventPage


class EventsAdminGroup(ModelAdminGroup):
    menu_label = "Events"
    items = (EventPageAdmin, SingleEventPageAdmin)
    menu_order = 400


modeladmin_register(AuthorModelAdmin)
modeladmin_register(BookModelAdmin)
modeladmin_register(EventsAdminGroup)
