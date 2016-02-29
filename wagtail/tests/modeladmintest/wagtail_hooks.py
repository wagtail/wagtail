from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminThumbMixin, ModelAdminGroup, modeladmin_register)
from .models import Author, Book
from .testapp import EventPage, SingleEventPage

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


class EventPageAdmin(ModelAdminThumbMixin, ModelAdmin):
    model = EventPage
    thumb_image_field_name = 'feed_image'
    list_display = ('admin_thumb', 'title', 'date_from', 'audience')
    list_display_add_buttons = 'title'


class SingleEventPageAdmin(EventPageAdmin):
    model = SingleEventPage


class EventsAdminGroup(ModelAdminGroup):
    menu_label = "Events"
    items = (EventPageAdmin, SingleEventPageAdmin)
    menu_order = 400


modeladmin_register(AuthorModelAdmin)
modeladmin_register(BookModelAdmin)
modeladmin_register(EventsAdminGroup)
