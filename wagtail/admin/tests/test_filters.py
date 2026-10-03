from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.admin.filters import FilteredModelChoiceField
from wagtail.test.utils import WagtailTestUtils

User = get_user_model()


class TestFilteredModelChoiceField(WagtailTestUtils, TestCase):
    def setUp(self):
        self.musicians = Group.objects.create(name="Musicians")
        self.actors = Group.objects.create(name="Actors")

        self.david = self.create_user(
            "david",
            "david@example.com",
            "kn1ghtr1der",
            first_name="David",
            last_name="Hasselhoff",
        )
        self.david.groups.set([self.musicians, self.actors])

        self.kevin = self.create_user(
            "kevin",
            "kevin@example.com",
            "6degrees",
            first_name="Kevin",
            last_name="Bacon",
        )
        self.kevin.groups.set([self.actors])

        self.morten = self.create_user(
            "morten",
            "morten@example.com",
            "t4ke0nm3",
            first_name="Morten",
            last_name="Harket",
        )
        self.morten.groups.set([self.musicians])

    def test_with_relation(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="id_group",
                filter_accessor="groups",
            )

        form = UserForm()
        html = str(form["users"])
        options_data = [
            (
                self.david.pk,
                self.david.get_username(),
                [self.musicians.pk, self.actors.pk],
            ),
            (self.kevin.pk, self.kevin.get_username(), [self.actors.pk]),
            (self.morten.pk, self.morten.get_username(), [self.musicians.pk]),
        ]
        soup = self.get_soup(html)
        select = soup.select_one("select[name=users]")
        self.assertIsNotNone(select)
        self.assertLessEqual(
            {
                "data-widget": "filtered-select",
                "data-filter-field": "id_group",
                "required": "",
                "id": "id_users",
            }.items(),
            select.attrs.items(),
        )
        options = select.select("option")
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0].get("value"), "")
        for option, (value, text, filter_values) in zip(options[1:], options_data):
            self.assertEqual(option.get("value"), str(value))
            self.assertEqual(option.text, text)
            # No ordering guarantee, so use assertCountEqual
            self.assertCountEqual(
                option.get("data-filter-value").split(","),
                [str(filter_value) for filter_value in filter_values],
            )

    def test_with_callable(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="id_group",
                filter_accessor=lambda user: user.groups.all().order_by("name"),
            )

        form = UserForm()
        html = str(form["users"])

        options_data = [
            (
                self.david.pk,
                self.david.get_username(),
                [self.actors.pk, self.musicians.pk],
            ),
            (self.kevin.pk, self.kevin.get_username(), [self.actors.pk]),
            (self.morten.pk, self.morten.get_username(), [self.musicians.pk]),
        ]
        soup = self.get_soup(html)
        select = soup.select_one("select[name=users]")
        self.assertIsNotNone(select)
        self.assertLessEqual(
            {
                "data-widget": "filtered-select",
                "data-filter-field": "id_group",
                "required": "",
                "id": "id_users",
            }.items(),
            select.attrs.items(),
        )
        options = select.select("option")
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0].get("value"), "")
        for option, (value, text, filter_values) in zip(options[1:], options_data):
            self.assertEqual(option.get("value"), str(value))
            self.assertEqual(option.text, text)
            self.assertEqual(
                option.get("data-filter-value").split(","),
                [str(filter_value) for filter_value in filter_values],
            )
