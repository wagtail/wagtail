from typing import Union

from django.test import SimpleTestCase

from .wagtail_tests import WagtailTestUtils


class AdminTemplateTestUtils:
    base_breadcrumb_items = [{"label": "Home", "url": "/admin/"}]

    def assertBreadcrumbsItemsRendered(
        self: Union[WagtailTestUtils, SimpleTestCase],
        items: list[dict[str, str]],
        html: Union[str, bytes],
    ):
        soup = self.get_soup(html)
        # Select with a class instead of a data-controller attribute because
        # the controller is only applied if the breadcrumbs are collapsible
        breadcrumbs = soup.select(".w-breadcrumbs")
        num_breadcrumbs = len(breadcrumbs)
        self.assertEqual(
            num_breadcrumbs,
            1,
            f"Expected one breadcrumbs component to be rendered, found {num_breadcrumbs}",
        )
        items = self.base_breadcrumb_items + items
        rendered_items = breadcrumbs[0].select("ol > li")
        num_rendered_items = len(rendered_items)
        num_items = len(items)
        arrows = soup.select("ol > li > svg")
        num_arrows = len(arrows)
        self.assertEqual(
            num_rendered_items,
            num_items,
            f"Expected {num_items} breadcrumbs items to be rendered, found {num_rendered_items}",
        )
        self.assertEqual(
            num_arrows,
            num_items - 1,
            f"Expected {num_items - 1} arrows to be rendered, found {num_arrows}",
        )

        for item, rendered_item in zip(items, rendered_items):
            if item.get("url") is not None:
                element = rendered_item.select_one("a")
                self.assertIsNotNone(
                    element,
                    f"Expected '{item['label']}' breadcrumbs item to be a link",
                )
                self.assertEqual(
                    element["href"],
                    item["url"],
                    f"Expected '{item['label']}' breadcrumbs item to link to '{item['url']}'",
                )
            else:
                element = rendered_item.select_one("div")
                self.assertIsNotNone(
                    element,
                    f"Expected '{item['label']}' breadcrumbs item to be a div",
                )

            # Sublabel is optional and the : separator is invisible
            label = element.get_text(strip=True)
            sublabel = None
            if item.get("sublabel"):
                label, sublabel = label.split(":", maxsplit=1)

            self.assertEqual(
                label,
                item["label"],
                f"Expected '{item['label']}' breadcrumbs item label, found '{label}'",
            )

            if sublabel:
                self.assertEqual(
                    sublabel,
                    item["sublabel"],
                    f"Expected '{item['sublabel']}' breadcrumbs item sublabel, found '{sublabel}'",
                )

    def assertBreadcrumbsNotRendered(
        self: Union[WagtailTestUtils, SimpleTestCase],
        html: Union[str, bytes],
    ):
        soup = self.get_soup(html)
        # Select with a class instead of a data-controller attribute because
        # the controller is only applied if the breadcrumbs are collapsible
        breadcrumbs = soup.select_one(".w-breadcrumbs")
        # Confirmation views (e.g. delete view) shouldn't render breadcrumbs
        self.assertIsNone(breadcrumbs)
