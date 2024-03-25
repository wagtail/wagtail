from django.test import TestCase

from wagtail.test.testapp.models import (
    EventPage,
    ExtremeChallengeEventPage,
    FoodieEventPage,
)


class TestPageManager(TestCase):
    fixtures = ["test_specific.json"]

    def test_query_from_concrete_model_manager_includes_proxy_instances(self):
        all_events = EventPage.objects.live()
        self.assertEqual(
            tuple(e.title for e in all_events),
            (
                "Christmas",
                "Special event",
                "Conquer Everest (2022)",
                "Brecon Beacons Ultra (2022)",
                "Festive Feasters (2023)",
                "Vegan BBQ Bonanza (Spring '24)",
            ),
        )

    def test_query_from_proxy_model_manager_only_includes_instances_of_that_type(self):
        extreme_events = ExtremeChallengeEventPage.objects.all()
        self.assertEqual(
            tuple(e.title for e in extreme_events),
            ("Conquer Everest (2022)", "Brecon Beacons Ultra (2022)"),
        )

        foodie_events = FoodieEventPage.objects.all()
        self.assertEqual(
            tuple(e.title for e in foodie_events),
            ("Festive Feasters (2023)", "Vegan BBQ Bonanza (Spring '24)"),
        )
