from unittest import TestCase

from wagtail.admin.ui.side_panels import BaseSidePanel, BaseSidePanels


class SidePanelA(BaseSidePanel):
    order = 300


class SidePanelB(BaseSidePanel):
    order = 200


class SidePanelC(BaseSidePanel):
    order = 400


class MySidePanels(BaseSidePanels):
    def __init__(self, request, object):
        super().__init__(request, object)
        self.side_panels = [
            SidePanelA(object, request),
            SidePanelB(object, request),
            SidePanelC(object, request),
        ]


class TestSidePanels(TestCase):
    def test_ordering(self):
        panels = MySidePanels(None, None)
        self.assertSequenceEqual(
            [type(panel) for panel in panels],
            [SidePanelB, SidePanelA, SidePanelC],
        )
