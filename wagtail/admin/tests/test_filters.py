from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.admin.filters import FilteredModelChoiceField


User = get_user_model()


class TestFilteredModelChoiceField(TestCase):
    def setUp(self):
        self.musicians = Group.objects.create(name="Musicians")
        self.actors = Group.objects.create(name="Actors")

        self.david = User.objects.create_user(
            'david', 'david@example.com', 'kn1ghtr1der', first_name="David", last_name="Hasselhoff"
        )
        self.david.groups.set([self.musicians, self.actors])

        self.kevin = User.objects.create_user(
            'kevin', 'kevin@example.com', '6degrees', first_name="Kevin", last_name="Bacon"
        )
        self.kevin.groups.set([self.actors])

        self.morten = User.objects.create_user(
            'morten', 'morten@example.com', 't4ke0nm3', first_name="Morten", last_name="Harket"
        )
        self.morten.groups.set([self.musicians])

    def test_with_relation(self):

        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by('username'), filter_field='id_group', filter_accessor='groups'
            )

        form = UserForm()
        html = str(form['users'])
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="%(david)s" data-filter-value="%(musicians)s,%(actors)s">david</option>
                <option value="%(kevin)s" data-filter-value="%(actors)s">kevin</option>
                <option value="%(morten)s" data-filter-value="%(musicians)s">morten</option>
            </select>
        """ % {
            'david': self.david.pk, 'kevin': self.kevin.pk, 'morten': self.morten.pk,
            'musicians': self.musicians.pk, 'actors': self.actors.pk,
        }
        self.assertHTMLEqual(html, expected_html)

    def test_with_callable(self):

        class UserForm(forms.Form):
            users = FilteredModelChoiceField(
                queryset=User.objects.order_by('username'), filter_field='id_group',
                filter_accessor=lambda user: user.groups.all()
            )

        form = UserForm()
        html = str(form['users'])
        expected_html = """
            <select name="users" data-widget="filtered-select" data-filter-field="id_group" required id="id_users">
                <option value="" selected>---------</option>
                <option value="%(david)s" data-filter-value="%(musicians)s,%(actors)s">david</option>
                <option value="%(kevin)s" data-filter-value="%(actors)s">kevin</option>
                <option value="%(morten)s" data-filter-value="%(musicians)s">morten</option>
            </select>
        """ % {
            'david': self.david.pk, 'kevin': self.kevin.pk, 'morten': self.morten.pk,
            'musicians': self.musicians.pk, 'actors': self.actors.pk,
        }
        self.assertHTMLEqual(html, expected_html)
