from django.test import TestCase

from wagtail.contrib.redirects.forms import ConfirmImportForm, ImportForm


class TestImportForm(TestCase):
    def test_file_input_generates_proper_accept(self):
        form = ImportForm(["csv", "tsv"])
        self.assertIn('accept=".csv,.tsv"', form.as_table())


class TestConfirmImportForm(TestCase):
    def test_choices_get_appended_with_intro_label_if_multiple(self):
        form = ConfirmImportForm(headers=[(0, "From"), (1, "To")])
        first_choice = form.fields["from_index"].choices[0]
        self.assertEqual(first_choice[0], "")
        self.assertEqual(first_choice[1], "---")

    def test_choices_does_not_get_generated_label_if_single_choice(self):
        form = ConfirmImportForm(headers=[(1, "Hi")])
        first_choice = form.fields["from_index"].choices[0]
        self.assertNotEqual(first_choice[0], "")
        self.assertNotEqual(first_choice[1], "---")
