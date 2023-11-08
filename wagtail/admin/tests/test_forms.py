from django.forms.fields import CharField
from django.test import SimpleTestCase, TestCase

from wagtail.admin.forms.auth import LoginForm, PasswordResetForm


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
