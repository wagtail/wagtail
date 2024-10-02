import hashlib
import itertools
import re
from functools import lru_cache

from django.template.loader import render_to_string
from django.urls import reverse

from wagtail import hooks

icon_comment_pattern = re.compile(r"<!--.*?-->", re.DOTALL)


@lru_cache(maxsize=None)
def get_icons():
    icon_hooks = hooks.get_hooks("register_icons")
    all_icons = sorted(itertools.chain.from_iterable(hook([]) for hook in icon_hooks))
    combined_icon_markup = ""
    for icon in all_icons:
        symbol = (
            render_to_string(icon)
            .replace('xmlns="http://www.w3.org/2000/svg"', "")
            .replace("svg", "symbol")
        )
        symbol = icon_comment_pattern.sub("", symbol)
        combined_icon_markup += symbol

    return render_to_string(
        "wagtailadmin/shared/icons.html", {"icons": combined_icon_markup}
    )


@lru_cache(maxsize=None)
def get_icon_sprite_hash():
    return hashlib.sha1(get_icons().encode()).hexdigest()[:8]


def get_icon_sprite_url():
    return reverse("wagtailadmin_sprite") + f"?h={get_icon_sprite_hash()}"
