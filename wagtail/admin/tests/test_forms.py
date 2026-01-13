from django.forms.fields import CharField
from django.test import SimpleTestCase, TestCase

from wagtail.admin.forms.auth import LoginForm, PasswordResetForm
from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.test.testapp.models import Advert, CustomImage


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


class TestDeferredValidationProperty(TestCase):
    def test_deferred_validation_property(self):
        class CustomImageForm(WagtailAdminModelForm):
            def clean(self):
                cleaned_data = super().clean()

                if not self.is_deferred_validation:
                    if not cleaned_data.get("caption", "") and not cleaned_data.get(
                        "fancy_caption", ""
                    ):
                        self.add_error(
                            "caption", "Either caption or fancy_caption is required"
                        )
                        self.add_error(
                            "fancy_caption",
                            "Either caption or fancy_caption is required",
                        )
                return cleaned_data

            class Meta:
                model = CustomImage
                fields = ["caption", "fancy_caption"]

        # No deferred validation
        form = CustomImageForm(
            {
                "caption": "",
                "fancy_caption": "{}",
            }
        )
        self.assertFalse(form.is_valid())

        form = CustomImageForm(
            {
                "caption": "Minimal caption",
                "fancy_caption": "{}",
            }
        )
        self.assertTrue(form.is_valid())

        # Deferred validation
        form = CustomImageForm(
            {
                "caption": "",
                "fancy_caption": "{}",
            }
        )
        form.defer_required_fields()
        self.assertTrue(form.is_valid())

        # No deferred validation, when check is carried out
        form = CustomImageForm(
            {
                "caption": "",
                "fancy_caption": "{}",
            }
        )
        form.defer_required_fields()
        form.restore_required_fields()
        self.assertFalse(form.is_valid())

        form = CustomImageForm(
            {
                "caption": "Minimal caption",
                "fancy_caption": "{}",
            }
        )
        form.defer_required_fields()
        form.restore_required_fields()
        self.assertTrue(form.is_valid())
