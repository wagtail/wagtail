from functools import lru_cache
from pathlib import Path

from django.template import TemplateDoesNotExist
from django.template.loader import select_template

import wagtail


@lru_cache(maxsize=None)
def template_is_overridden(template_name: str, expected_location: str) -> bool:
    """
    Check if a template has been overridden.

    A template is overridden if the resolved template file is different from the
    expected location within the `wagtail` package directory.
    """
    try:
        template = select_template([template_name])
    except TemplateDoesNotExist:
        return False

    root = Path(wagtail.__file__).resolve().parent
    path = str(root / expected_location / template_name)

    return template.origin.name != path
