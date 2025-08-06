import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.filters import FilteredModelChoiceField
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.test.testapp.models import EventPage
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
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-filter-value="{musicians},{actors}">{david_username}</option>
                <option value="{kevin}" data-filter-value="{actors}">{kevin_username}</option>
                <option value="{morten}" data-filter-value="{musicians}">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=self.musicians.pk,
            actors=self.actors.pk,
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)

    def test_with_callable(self):
        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by(User.USERNAME_FIELD),
                filter_field="id_group",
                filter_accessor=lambda user: user.groups.all(),
            )

        form = UserForm()
        html = str(form["users"])
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="{david}" data-filter-value="{musicians},{actors}">{david_username}</option>
                <option value="{kevin}" data-filter-value="{actors}">{kevin_username}</option>
                <option value="{morten}" data-filter-value="{musicians}">{morten_username}</option>
            </select>
        """.format(
            david=self.david.pk,
            kevin=self.kevin.pk,
            morten=self.morten.pk,
            musicians=self.musicians.pk,
            actors=self.actors.pk,
            david_username=self.david.get_username(),
            kevin_username=self.kevin.get_username(),
            morten_username=self.morten.get_username(),
        )
        self.assertHTMLEqual(html, expected_html)


class TestUsageCountFilter(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

        image_model = get_image_model()

        self.image_1 = image_model.objects.create(
            title="Test image 1",
            file=get_test_image_file(),
        )
        self.image_2 = image_model.objects.create(
            title="Test image 2",
            file=get_test_image_file(),
        )
        self.image_3 = image_model.objects.create(
            title="Test image 3",
            file=get_test_image_file(),
        )

    def test_usage_count_filter_for_images(self):
        home_page = Page.objects.get(id=2)

        # image_1: used in 1 page

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_1",
                    slug="test_page_1",
                    feed_image=self.image_1,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        # image_2: used in 2 pages

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_2",
                    slug="test_page_2",
                    feed_image=self.image_2,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_3",
                    slug="test_page_3",
                    feed_image=self.image_2,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        # image_3: used in 3 pages

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_4",
                    slug="test_page_4",
                    feed_image=self.image_3,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_5",
                    slug="test_page_5",
                    feed_image=self.image_3,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        with self.captureOnCommitCallbacks(execute=True):
            home_page.add_child(
                instance=EventPage(
                    title="test_page_6",
                    slug="test_page_6",
                    feed_image=self.image_3,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

        # This checks if only image_3 is returned when minimum usage count is set to 3

        response = self.client.get(
            reverse("wagtailimages:index"), {"usage_count_min": "3"}
        )
        self.assertEqual(response.status_code, 200)

        images = response.context["page_obj"].object_list
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0], self.image_3)

        # This checks if only image_1 and image_2 are returned when maximum usage count is set to 2

        response = self.client.get(
            reverse("wagtailimages:index"), {"usage_count_max": "2"}
        )
        self.assertEqual(response.status_code, 200)

        images = response.context["page_obj"].object_list
        self.assertEqual(len(images), 2)
        self.assertIn(self.image_1, images)
        self.assertIn(self.image_2, images)

        # This checks if only image_1 is returned when maximum usage count is set to 1

        response = self.client.get(
            reverse("wagtailimages:index"), {"usage_count_max": "1"}
        )
        self.assertEqual(response.status_code, 200)

        images = response.context["page_obj"].object_list
        self.assertEqual(len(images), 1)
        self.assertIn(self.image_1, images)
