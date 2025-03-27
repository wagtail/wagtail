from collections import namedtuple

# Represents a django-filter filter that is currently in force on a listing queryset
ActiveFilter = namedtuple(
    "ActiveFilter", ["auto_id", "field_label", "value", "removed_filter_url"]
)
