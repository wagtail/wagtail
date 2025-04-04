import json
import re
from typing import List, Optional, Tuple, Union

from django.conf import settings
from django.forms import widgets

from wagtail.coreutils import get_js_regex


class SlugInput(widgets.TextInput):
    """
    Associates the input field with the Stimulus w-slug (CleanController).
    Slugifies content based on ``WAGTAIL_ALLOW_UNICODE_SLUGS`` and supports
    fields syncing their value to this field (see `TitleFieldPanel`) if used.
    Allows the ability to define the ``locale`` to allow locale (language code)
    specific transliteration, or ``formatters`` for more custom handling.
    """

    def __init__(
        self,
        attrs: Optional[dict] = None,
        formatters: Optional[
            List[
                Tuple[
                    Union[re.Pattern, str, bytes],
                    Optional[str],
                ],
            ]
        ] = [],
        locale: Optional[object] = None,
    ):
        default_attrs = {
            "data-controller": "w-slug",
            "data-action": "blur->w-slug#slugify w-sync:check->w-slug#compare w-sync:apply->w-slug#urlify:prevent",
            "data-w-slug-allow-unicode-value": getattr(
                settings, "WAGTAIL_ALLOW_UNICODE_SLUGS", True
            ),
            "data-w-slug-compare-as-param": "urlify",
            "data-w-slug-trim-value": "true",
        }

        if formatters:
            # If formatters are provided, parse them into a JSON string
            # Support flexible input of regex, replace, and flags
            parsed_formatters = []
            for item in formatters:
                if isinstance(item, (list, tuple)):
                    regex_args = [item[0]]
                    replace = item[1] if len(item) > 1 else ""
                    if len(item) == 3:
                        # If base_js_flags are provided, add them to the regex_args
                        regex_args.append(item[2])
                else:
                    regex_args = [item]
                    replace = ""
                parsed_formatters.append([get_js_regex(*regex_args), replace])
            default_attrs["data-w-slug-formatters-value"] = json.dumps(
                parsed_formatters,
                separators=(",", ":"),
            )

        if locale is not None:
            # Attempt to resolve a non-empty locale string from a `Locale` instance or the string itself.
            # If no locale can be found, use 'und' - as per ISO639-2 standard, 'und' represents 'undetermined'.
            # If the attribute is not set, the input will fall back to the ``ACTIVE_LOCALE`` or document lang within the CleanController.
            default_attrs["data-w-slug-locale-value"] = (
                getattr(locale, "language_code", locale) or "und"
            )

        if attrs:
            default_attrs.update(attrs)

        super().__init__(default_attrs)
