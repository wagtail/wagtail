from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

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

    def __str__(self):
        return self.title
