from django.core.paginator import Paginator
from django.test import TestCase, override_settings

from wagtail.admin.paginator import WagtailPaginator, get_wagtail_paginator_class


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
            # (total pages, current page, [expected elided page range])
            (1, 1, [1]),

            (3, 1, [1, 2, 3]),
            (3, 2, [1, 2, 3]),
            (3, 3, [1, 2, 3]),

            (10, 1, [1, 2, 3, 4, ellipsis, 10]),
            (10, 6, [1, ellipsis, 6, 7, ellipsis, 10]),
            (10, 10, [1, ellipsis, 7, 8, 9, 10]),

            # Exmaples of test cases that should fail
            # (3, 1, [1, 2]), # Too few pages
            # (10, 1, [1, 2, 3, 4, ellipsis, 9, 10]), # Too many pages
            # (10, 6, [1, ellipsis, 5, 6, ellipsis, 10]), # Wrong middle position
            # (10, 10, [1, ellipsis, 7, 8, 9]), # Too few pages
        ]
        
        for total_pages, current_page, expected_elided_page_range in test_cases:
            paginator = WagtailPaginator(list(range(total_pages)), 1) # 1 object per page
            elided_page_range = paginator.get_elided_page_range(current_page)
            self.assertSequenceEqual(
                list(elided_page_range),
                expected_elided_page_range,
                f"Elided page range failed for total_pages={total_pages}, current_page={current_page}"
            )


class TestGetWagtailPaginatorClass(TestCase):

    def test_default_paginator_class(self):
        # Test that the default paginator is WagtailPaginator when no setting is provided
        self.assertIs(get_wagtail_paginator_class(), WagtailPaginator)

    @override_settings(WAGTAILADMIN_PAGINATOR_CLASS="django.core.paginator.Paginator")
    def test_get_paginator_class(self):
        # Test that the provided setting is a subclass of Paginator
        self.assertIs(get_wagtail_paginator_class(), Paginator)

    @override_settings(WAGTAILADMIN_PAGINATOR_CLASS="myapp.is.not.real.Paginator")
    def test_invalid_paginator_class(self):
        # Test handling of invalid class path
        with self.assertRaises(ImportError):
            get_wagtail_paginator_class()
