from django.shortcuts import render
from django.utils.translation import gettext as _

from wagtail.admin.utils import get_block_usage


def block_usage(request):
    return render(
        request,
        "wagtailadmin/reports/block_usage.html",
        {
            "title": _("Block usage"),
            "blocks": [(block.label, usage) for block, usage in get_block_usage()],
        },
    )
