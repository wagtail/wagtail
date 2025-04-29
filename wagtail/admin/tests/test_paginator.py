from django.test import TestCase

from wagtail.admin.paginator import WagtailPaginator


class TestWagtailPaginator(TestCase):
    def test_elided_page_range(self):
        """
        Test the get_elided_page_range method of WagtailPaginator.

        For example, if there are 10 pages, the output should be:
        At page 1:  1 2 3 4 … 10
        At page 6:  1 … 6 7 … 10
        At page 10: 1 … 7 8 9 10
        """

        ellipsis = WagtailPaginator.ELLIPSIS

        test_cases = [
            # Format: (total pages, current page, num_page_buttons, [expected elided page range])
            # Examples of test cases that should fail:
            # (3, 1, 6, [1, 2]), # Too few pages
            # (10, 1, 6, [1, 2, 3, 4, ellipsis, 9, 10]), # Too many pages
            # (10, 6, 6, [1, ellipsis, 5, 6, ellipsis, 10]), # Wrong middle position
            # (10, 10, 6, [1, ellipsis, 7, 8, 9]), # Too few pages
            # num_page_buttons=4
            # If the number of page buttons is less than 5, the elided range should be empty.
            (10, 3, 4, []),
            # num_page_buttons=5
            (1, 1, 5, [1]),
            (3, 1, 5, [1, 2, 3]),
            (3, 3, 5, [1, 2, 3]),
            (5, 2, 5, [1, 2, 3, 4, 5]),
            (10, 1, 5, [1, 2, 3, ellipsis, 10]),
            (10, 6, 5, [1, ellipsis, 6, ellipsis, 10]),
            (10, 10, 5, [1, ellipsis, 8, 9, 10]),
            # Our default number of page buttons.
            # num_page_buttons=6
            (1, 1, 6, [1]),
            (3, 1, 6, [1, 2, 3]),
            (3, 3, 6, [1, 2, 3]),
            (6, 2, 6, [1, 2, 3, 4, 5, 6]),
            (6, 6, 6, [1, 2, 3, 4, 5, 6]),
            (10, 1, 6, [1, 2, 3, 4, ellipsis, 10]),
            (10, 6, 6, [1, ellipsis, 6, 7, ellipsis, 10]),
            (10, 10, 6, [1, ellipsis, 7, 8, 9, 10]),
            # num_page_buttons=7
            (7, 2, 7, [1, 2, 3, 4, 5, 6, 7]),
            (10, 1, 7, [1, 2, 3, 4, 5, ellipsis, 10]),
            (10, 6, 7, [1, ellipsis, 5, 6, 7, ellipsis, 10]),
            (10, 10, 7, [1, ellipsis, 6, 7, 8, 9, 10]),
            # num_page_buttons=8
            (8, 3, 8, [1, 2, 3, 4, 5, 6, 7, 8]),
            (10, 1, 8, [1, 2, 3, 4, 5, 6, ellipsis, 10]),
            (20, 6, 8, [1, ellipsis, 5, 6, 7, 8, ellipsis, 20]),
            (10, 10, 8, [1, ellipsis, 5, 6, 7, 8, 9, 10]),
            # num_page_buttons=9
            (9, 3, 9, [1, 2, 3, 4, 5, 6, 7, 8, 9]),
            (10, 1, 9, [1, 2, 3, 4, 5, 6, 7, ellipsis, 10]),
            (10, 6, 9, [1, ellipsis, 4, 5, 6, 7, 8, 9, 10]),
            (20, 6, 9, [1, ellipsis, 4, 5, 6, 7, 8, ellipsis, 20]),
            (10, 10, 9, [1, ellipsis, 4, 5, 6, 7, 8, 9, 10]),
            # num_page_buttons=10
            (10, 3, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            (10, 1, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            (10, 6, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            (20, 6, 10, [1, ellipsis, 4, 5, 6, 7, 8, 9, ellipsis, 20]),
            (10, 10, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        ]

        for (
            total_pages,
            current_page,
            num_page_buttons,
            expected_elided_page_range,
        ) in test_cases:
            paginator = WagtailPaginator(
                list(range(total_pages)), 1
            )  # 1 object per page
            paginator.num_page_buttons = num_page_buttons
            elided_page_range = paginator.get_elided_page_range(current_page)
            self.assertSequenceEqual(
                list(elided_page_range),
                expected_elided_page_range,
                f"Elided page range failed for total_pages={total_pages}, current_page={current_page}, num_page_buttons={num_page_buttons}",
            )
