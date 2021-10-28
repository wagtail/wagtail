from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel, MultiFieldPanel, ObjectList, PageChooserPanel, TabbedInterface)
from wagtail.core.models import Page
from wagtail.search import index


class Author(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    def author_birth_string(self):
        return 'This author was born in pallet town'

    author_birth_string.short_description = "Birth information"

    def __str__(self):
        return self.name

    def first_book(self):
        # For testing use of object methods in list_display
        book = self.book_set.first()
        if book:
            return book.title
        return ''


class Book(models.Model, index.Indexed):
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    cover_image = models.ForeignKey('wagtailimages.Image', on_delete=models.SET_NULL, null=True, blank=True)

    search_fields = [
        index.SearchField('title'),
        index.FilterField('title'),
        index.FilterField('id'),
    ]

    def __str__(self):
        return self.title


class SoloBook(models.Model):
    author = models.OneToOneField(Author, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Token(models.Model):
    key = models.CharField(max_length=40, primary_key=True)

    def __str__(self):
        return self.key


class Publisher(models.Model):
    name = models.CharField(max_length=50)
    headquartered_in = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name


class VenuePage(Page):
    address = models.CharField(max_length=300)
    capacity = models.IntegerField()


class Visitor(models.Model):
    """model used to test modeladmin.edit_handler usage in get_edit_handler"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name


class Contributor(models.Model):
    """model used to test modeladmin.panels usage in get_edit_handler"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.first_name


class Person(models.Model):
    """model used to test model.edit_handlers usage in get_edit_handler"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('phone_number'),
    ]
    edit_handler = TabbedInterface([
        ObjectList(panels),
    ])

    def __str__(self):
        return self.first_name


class Friend(models.Model):
    """model used to test model.panels usage in get_edit_handler"""
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    panels = [
        FieldPanel('first_name'),
        FieldPanel('phone_number'),
    ]

    def __str__(self):
        return self.first_name


class RelatedLink(models.Model):
    title = models.CharField(
        max_length=255,
    )
    link = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='+'
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel('title'),
                PageChooserPanel('link'),
            ],
            heading='Related Link'
        ),
    ]
