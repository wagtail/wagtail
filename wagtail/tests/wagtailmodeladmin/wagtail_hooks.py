from wagtail.contrib.modeladmin.options import ModelAdmin, wagtailmodeladmin_register
from .models import Author, Book


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


wagtailmodeladmin_register(AuthorModelAdmin)
wagtailmodeladmin_register(BookModelAdmin)
