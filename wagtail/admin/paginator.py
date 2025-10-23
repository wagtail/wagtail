from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.functional import cached_property
from django.utils.translation import gettext as _


class WagtailPaginator(Paginator):
    num_page_buttons = 6

    @cached_property
    def model(self):
        return getattr(self.object_list, "model", None)

    @cached_property
    def verbose_name(self):
        if self.model:
            return self.model._meta.verbose_name
        return _("item")

    @cached_property
    def verbose_name_plural(self):
        if self.model:
            return self.model._meta.verbose_name_plural
        return _("items")

    @cached_property
    def items_count_label(self):
        if self.count == 1:
            return f"1 {self.verbose_name}"
        else:
            return f"{self.count} {self.verbose_name_plural}"

    def get_elided_page_range(self, page_number):
        """
        Provides a range of page numbers where the number of positions
        occupied by page numbers and ellipses is fixed to num_page_buttons.

        For example, if there are 10 pages where num_page_buttons is 6, the output will be:
        At page 1:  1 2 3 4 … 10
        At page 6:  1 … 6 7 … 10
        At page 10: 1 … 7 8 9 10

        The paginator will show the current page in the middle (odd number of buttons)
        or to the left side of the middle (even number of buttons).
        """

        try:
            number = self.validate_number(page_number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = self.num_pages

        if self.num_page_buttons < 5:
            # We provide no page range if fewer than 5 num_page_buttons.
            # This displays only "Previous" and "Next" buttons.
            return []

        # Provide all page numbers if fewer than num_page_buttons.
        if self.num_pages <= self.num_page_buttons:
            yield from self.page_range
            return

        # These thresholds are the maximum number of buttons
        # that can be shown on the start or end of the page range
        # before the middle part of the range expands.
        # For even num_page_buttons values both thresholds are the same.
        # For odd num_page_buttons values the start threshold is one more than the end threshold.
        end_threshold = self.num_page_buttons // 2
        start_threshold = end_threshold + (self.num_page_buttons % 2)

        # Show the first page.
        yield 1

        # Show middle pages.
        if number <= start_threshold:
            # Result: 1 [ 2 3 4 … ] 10
            yield from range(2, self.num_page_buttons - 1)
            yield self.ELLIPSIS
        elif number < self.num_pages - end_threshold:
            # Result: 1 [ … 5 6* 7 … ] 10
            # 4 spaces are occupied by first/last page numbers and ellipses
            middle_size = self.num_page_buttons - 4
            offset = (middle_size - 1) // 2
            yield self.ELLIPSIS
            yield from range(number - offset, number + middle_size - offset)
            yield self.ELLIPSIS
        else:
            # Result: 1 [ … 7 8 9 ] 10
            yield self.ELLIPSIS
            yield from range(
                self.num_pages - (self.num_page_buttons - 3), self.num_pages
            )

        # Show the last page.
        yield self.num_pages
