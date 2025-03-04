from django.forms.fields import CharField
from django.test import SimpleTestCase, TestCase

from wagtail.admin.forms.auth import LoginForm, PasswordResetForm
from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.test.testapp.models import Advert


class CustomLoginForm(LoginForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("captcha") == "solved":
            self.add_error(None, "Captcha is invalid")
        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")


class TestLoginForm(TestCase):
    def test_extra_fields(self):
        form = CustomLoginForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestPasswordResetForm(SimpleTestCase):
    def test_extra_fields(self):
        form = CustomPasswordResetForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestDeferRequiredFields(TestCase):
    def test_defer_required_fields(self):
        class AdvertForm(WagtailAdminModelForm):
            class Meta:
                model = Advert
                fields = ["url", "text"]
                defer_required_on_fields = ["text"]

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        self.assertFalse(form.is_valid())

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        form.defer_required_fields()
        self.assertTrue(form.is_valid())

        form = AdvertForm(
            {
                "url": "https://www.example.com",
                "text": "",
            }
        )
        form.defer_required_fields()
        form.restore_required_fields()
        self.assertFalse(form.is_valid())
