from django import template

from .wagtailembeds import embed_tag


register = template.Library()

register.simple_tag(name='embed')(embed_tag)
