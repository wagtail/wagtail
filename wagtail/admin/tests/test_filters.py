import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.filters import FilteredModelChoiceField
from wagtail.documents import get_document_model
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page
from wagtail.test.testapp.models import EventPage, EventPageRelatedLink
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
        document_model = get_document_model()

        self.home_page = Page.objects.get(id=2)

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

        self.document_1 = document_model.objects.create(
            title="Test document 1",
            file=get_test_document_file(),
        )
        self.document_2 = document_model.objects.create(
            title="Test document 2",
            file=get_test_document_file(),
        )
        self.document_3 = document_model.objects.create(
            title="Test document 3",
            file=get_test_document_file(),
        )

    # Helper method to create a page with a feed image
    def _create_page_with_image(self, title, slug, image):
        with self.captureOnCommitCallbacks(execute=True):
            self.home_page.add_child(
                instance=EventPage(
                    title=title,
                    slug=slug,
                    feed_image=image,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            ).save_revision().publish()

    # Helper method to create a page with a linked document
    def _create_page_with_document(self, title, slug, document):
        with self.captureOnCommitCallbacks(execute=True):
            event_page = self.home_page.add_child(
                instance=EventPage(
                    title=title,
                    slug=slug,
                    date_from=datetime.date.today(),
                    audience="private",
                    location="Test",
                    cost="Test",
                )
            )
            event_page.save_revision().publish()

            # Create a related link that links to the document
            related_link = EventPageRelatedLink()
            related_link.page = event_page
            related_link.title = f"Link to {document.title}"
            related_link.link_document = document
            related_link.save()

    def test_usage_count_filter_for_images(self):
        # image_1: used in 1 page
        self._create_page_with_image("test_page_1", "test_page_1", self.image_1)

        # image_2: used in 2 pages
        self._create_page_with_image("test_page_2", "test_page_2", self.image_2)
        self._create_page_with_image("test_page_3", "test_page_3", self.image_2)

        # image_3: used in 3 pages
        self._create_page_with_image("test_page_4", "test_page_4", self.image_3)
        self._create_page_with_image("test_page_5", "test_page_5", self.image_3)
        self._create_page_with_image("test_page_6", "test_page_6", self.image_3)

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

    def test_usage_count_filter_for_documents(self):
        # document_1: used in 1 page
        self._create_page_with_document("test_page_1", "test_page_1", self.document_1)

        # document_2: used in 2 pages
        self._create_page_with_document("test_page_2", "test_page_2", self.document_2)
        self._create_page_with_document("test_page_3", "test_page_3", self.document_2)

        # document_3: used in 3 pages
        self._create_page_with_document("test_page_4", "test_page_4", self.document_3)
        self._create_page_with_document("test_page_5", "test_page_5", self.document_3)
        self._create_page_with_document("test_page_6", "test_page_6", self.document_3)

        # This checks if only document_3 is returned when minimum usage count is set to 3
        response = self.client.get(
            reverse("wagtaildocs:index"), {"usage_count_min": "3"}
        )
        self.assertEqual(response.status_code, 200)

        documents = response.context["page_obj"].object_list
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0], self.document_3)

        # This checks if only document_1 and document_2 are returned when maximum usage count is set to 2
        response = self.client.get(
            reverse("wagtaildocs:index"), {"usage_count_max": "2"}
        )
        self.assertEqual(response.status_code, 200)

        documents = response.context["page_obj"].object_list
        self.assertEqual(len(documents), 2)
        self.assertIn(self.document_1, documents)
        self.assertIn(self.document_2, documents)

        # This checks if only document_1 is returned when maximum usage count is set to 1
        response = self.client.get(
            reverse("wagtaildocs:index"), {"usage_count_max": "1"}
        )
        self.assertEqual(response.status_code, 200)

        documents = response.context["page_obj"].object_list
        self.assertEqual(len(documents), 1)
        self.assertIn(self.document_1, documents)
