from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from wagtail.wagtailsnippets.models import register_snippet


# AlphaSnippet and ZuluSnippet are for testing ordering of
# snippets when registering.  They are named as such to ensure
# thier ordering is clear.  They are registered during testing
# to ensure specific [in]correct register ordering

# AlphaSnippet is registered during TestSnippetOrdering
@python_2_unicode_compatible
class AlphaSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


# ZuluSnippet is registered during TestSnippetOrdering
@python_2_unicode_compatible
class ZuluSnippet(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text


# Register model as snippet using register_snippet as both a function and a decorator

class RegisterFunction(models.Model):
    pass
register_snippet(RegisterFunction)

@register_snippet
class RegisterDecorator(models.Model):
    pass

