from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.module_loading import import_string


class WagtailPaginator(Paginator):
    def get_elided_page_range(self, page_number):
        """
        Provides a range of page numbers where the number of positions
        occupied by page numbers and ellipses is fixed to 6.

        For example, if there are 10 pages, the output will be:
        At page 1:  1 2 3 4 … 10
        At page 6:  1 … 6 7 … 10
        At page 10: 1 … 7 8 9 10
        """

        try:
            number = self.validate_number(page_number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = self.num_pages

        # Provide all page numbers if 6 or fewer.
        if self.num_pages <= 6:
            yield from self.page_range
            return

        # Show the first page.
        yield 1

        # Show middle pages.
        if number <= 3:
            yield from range(2, 5)
            yield self.ELLIPSIS
        elif number > 3 and number < self.num_pages - 3:
            yield self.ELLIPSIS
            yield from range(number, number + 2)
            yield self.ELLIPSIS
        else:
            yield self.ELLIPSIS
            yield from range(self.num_pages - 3, self.num_pages)

        # Show the last page.
        yield self.num_pages


def get_wagtail_paginator_class():
    """
    Get the paginator class from the ``WAGTAILADMIN_PAGINATOR_CLASS`` setting,
    which allows developers to provide a custom paginator class.
    Defaults to the ``WagtailPaginator`` class if not defined.
    """
    paginator_class_override = getattr(settings, "WAGTAILADMIN_PAGINATOR_CLASS", "")
    if paginator_class_override:
        paginator_class = import_string(paginator_class_override)
    else:
        paginator_class = WagtailPaginator

    return paginator_class
