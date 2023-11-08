# Alias for the update_index command, to avoid clashes with other packages
# that implement an update_index command (such as django-haystack)

from wagtail.search.management.commands.update_index import Command  # NOQA: F401
