from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.safestring import mark_safe

from wagtail.wagtailsearch import index
from treebeard.mp_tree import MP_Node


@python_2_unicode_compatible
class Author(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Book(models.Model, index.Indexed):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class TreebeardCategory(MP_Node):
    name = models.CharField(max_length=250)
    node_order_by = ['name']

    def hierarchical_name(self):
        bits = []
        for ancestor in self.get_ancestors().values('name'):
            bits.append(ancestor['name'])
        bits.append(self.name)
        return mark_safe('&nbsp;&nbsp;>&nbsp;&nbsp;'.join(bits))

    def __str__(self):
        return self.hierarchical_name()
