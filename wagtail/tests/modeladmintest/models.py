from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index


@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Book(models.Model, index.Indexed):
    author = models.ForeignKey(Author, on_delete=models.PROTECT)
    title = models.CharField(max_length=255)
    cover_image = models.ForeignKey('wagtailimages.Image', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Token(models.Model):
    key = models.CharField(max_length=40, primary_key=True)

    def __str__(self):
        return self.key


@python_2_unicode_compatible
class Publisher(models.Model):
    name = models.CharField(max_length=50)
    headquartered_in = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name


class VenuePage(Page):
    address = models.CharField(max_length=300)
    capacity = models.IntegerField()
