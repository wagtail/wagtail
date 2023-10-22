import json

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils.html import escape

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
                filter_field="group",
                filter_accessor="groups",
            )

        form = UserForm()
        html = str(form["users"])
        expected_html = """
            <select name="users" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-match="{musicians_and_actors}" data-w-cond-target="enable show">{david_username}</option>
                <option value="{kevin}" data-match="{actors}" data-w-cond-target="enable show">{kevin_username}</option>
                <option value="{morten}" data-match="{musicians}" data-w-cond-target="enable show">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=escape(json.dumps({"group": [None, str(self.musicians.pk)]})),
            actors=escape(json.dumps({"group": [None, str(self.actors.pk)]})),
            musicians_and_actors=escape(
                json.dumps(
                    {"group": [None, str(self.musicians.pk), str(self.actors.pk)]}
                )
            ),
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)

    def test_with_callable(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="group",
                filter_accessor=lambda user: user.groups.all(),
            )

        form = UserForm()
        html = str(form["users"])
        expected_html = """
            <select name="users" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-match="{musicians_and_actors}" data-w-cond-target="enable show">{david_username}</option>
                <option value="{kevin}" data-match="{actors}" data-w-cond-target="enable show">{kevin_username}</option>
                <option value="{morten}" data-match="{musicians}" data-w-cond-target="enable show">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=escape(json.dumps({"group": [None, str(self.musicians.pk)]})),
            actors=escape(json.dumps({"group": [None, str(self.actors.pk)]})),
            musicians_and_actors=escape(
                json.dumps(
                    {"group": [None, str(self.musicians.pk), str(self.actors.pk)]}
                )
            ),
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)
