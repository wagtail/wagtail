from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.core.models import Orderable, Page
from wagtail.search import index



class Author(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

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

    content_panels = Page.content_panels + [
        FieldPanel('address'),
        FieldPanel('capacity'),
        InlinePanel('related_seating_sections'),
    ]


class VenuePageRelatedSeatingSection(Orderable):
    name = models.CharField(max_length=50)
    seats = models.IntegerField()
    page = models.ForeignKey(
        VenuePage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_seating_sections'
    )

    panels = [FieldPanel('name'), FieldPanel('seats')]


class EventSupplier(models.Model):
    name = models.CharField(max_length=50)
    services = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)


class SocialMediaCampaign(models.Model):
    name = models.CharField(max_length=50)
    caption = models.CharField(max_length=255, blank=True)
    artwork = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def __str__(self):
        return self.name


class PrintMediaCampaign(models.Model):
    name = models.CharField(max_length=50)
    copy = models.CharField(max_length=255, blank=True)
    artwork = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    def __str__(self):
        return self.name
