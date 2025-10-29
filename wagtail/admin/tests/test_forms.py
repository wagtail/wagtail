import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.fields import CharField
from django.test import SimpleTestCase, TestCase
from PIL import Image

from wagtail.admin.forms.account import AvatarPreferencesForm
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


class TestAvatarPreferencesForm(TestCase):
    def create_image_file(self, size=(800, 800), color="red", name="test.jpg"):
        img = Image.new("RGB", size, color=color)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format="JPEG")
        img_byte_arr.seek(0)
        return SimpleUploadedFile(
            name=name, content=img_byte_arr.read(), content_type="image/jpeg"
        )

    def test_avatar_resize_large_square_image(self):
        uploaded_file = self.create_image_file(size=(800, 800), name="large_image.jpg")
        form = AvatarPreferencesForm(files={"avatar": uploaded_file})
        self.assertTrue(form.is_valid())

        avatar_file = form.clean_avatar()
        resized_image = Image.open(avatar_file)

        self.assertEqual(resized_image.size, (400, 400))

    def test_avatar_no_resize_small_image(self):
        uploaded_file = self.create_image_file(size=(300, 300), name="small_image.jpg")
        form = AvatarPreferencesForm(files={"avatar": uploaded_file})
        self.assertTrue(form.is_valid())

        avatar_file = form.clean_avatar()
        original_image = Image.open(avatar_file)

        self.assertEqual(original_image.size, (300, 300))

    def test_avatar_resize_width_greater_than_height(self):
        uploaded_file = self.create_image_file(size=(500, 300), name="wide_image.jpg")
        form = AvatarPreferencesForm(files={"avatar": uploaded_file})
        self.assertTrue(form.is_valid())

        avatar_file = form.clean_avatar()
        resized_image = Image.open(avatar_file)

        self.assertEqual(resized_image.width, 400)
        self.assertLessEqual(resized_image.height, 400)

        original_ratio = 500 / 300
        new_ratio = resized_image.width / resized_image.height
        self.assertAlmostEqual(original_ratio, new_ratio, places=2)

    def test_avatar_resize_height_greater_than_width(self):
        uploaded_file = self.create_image_file(size=(300, 500), name="tall_image.jpg")
        form = AvatarPreferencesForm(files={"avatar": uploaded_file})
        self.assertTrue(form.is_valid())

        avatar_file = form.clean_avatar()
        resized_image = Image.open(avatar_file)

        self.assertEqual(resized_image.height, 400)
        self.assertLessEqual(resized_image.width, 400)

        original_ratio = 300 / 500
        new_ratio = resized_image.width / resized_image.height
        self.assertAlmostEqual(original_ratio, new_ratio, places=2)
