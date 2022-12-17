from warnings import warn

from wagtail.coreutils import (  # noqa
    SCRIPT_RE,
    SLUGIFY_RE,
    WAGTAIL_APPEND_SLASH,
    InvokeViaAttributeShortcut,
    accepts_kwarg,
    camelcase_to_underscore,
    cautious_slugify,
    escape_script,
    find_available_slug,
    get_content_languages,
    get_content_type_label,
    get_model_string,
    get_supported_content_language_variant,
    multigetattr,
    resolve_model_string,
    safe_snake_case,
    string_to_ascii,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.utils is deprecated. "
    "Use wagtail.coreutils instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
