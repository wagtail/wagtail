from collections import Counter
from warnings import warn

from django.apps import apps
from django.conf import settings

from wagtail.fields import StreamField
from wagtail.utils.deprecation import RemovedInWagtail50Warning


def get_admin_base_url():
    """
    Gets the base URL for the wagtail admin site. This is set in `settings.WAGTAILADMIN_BASE_URL`,
    which was previously `settings.BASE_URL`.
    """

    admin_base_url = getattr(settings, "WAGTAILADMIN_BASE_URL", None)
    if admin_base_url is None and hasattr(settings, "BASE_URL"):
        warn(
            "settings.BASE_URL has been renamed to settings.WAGTAILADMIN_BASE_URL",
            category=RemovedInWagtail50Warning,
        )
        admin_base_url = settings.BASE_URL

    return admin_base_url


def get_block_usage():
    """
    Scans all StreamFields in the database and counts the number of times each block type has been used.

    Returns:
        A list of 2-tuples (block, usage_count) where 'block' is an instance of a Block and the usage_count
        is the number of times that block has been used.
    """
    blocks = {}
    counter = Counter()

    for model in apps.get_models():
        stream_fields = [
            field
            for field in model._meta.get_fields()
            if isinstance(field, StreamField)
        ]

        if not stream_fields:
            continue

        for stream_values in model.objects.all().values_list(
            *[field.name for field in stream_fields]
        ):
            for stream_value in stream_values:
                blocks.update({id(block.block): block.block for block in stream_value})
                counter.update(id(block.block) for block in stream_value)

    return [
        (blocks[block], usage_count) for block, usage_count in counter.most_common()
    ]
