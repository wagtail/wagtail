from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms.fields import CharField, ImageField
from django.test import SimpleTestCase, TestCase
from PIL import Image, ImageDraw

from wagtail.admin.forms.account import AvatarPreferencesForm
from wagtail.admin.forms.auth import LoginForm, PasswordResetForm
from wagtail.utils.utils import reduce_image_dimension


class CustomLoginForm(LoginForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("captcha") == "solved":
            self.add_error(None, "Captcha is invalid")
        return cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    captcha = CharField(label="Captcha", help_text="should be in extra_fields()")


class CustomImageField(ImageField):
    def to_python(self, data):
        avatar = data
        avatar.image = Image.open(avatar)
        avatar.content_type = "image/png"
        avatar.seek(0)
        return avatar


class CustomAvatarPreferenceForm(AvatarPreferencesForm):
    avatar = CustomImageField(required=False)

    image_holder = None

    def clean(self):
        return self.cleaned_data

    def save(self):
        avatar = self.cleaned_data["avatar"]
        updated_avatar = reduce_image_dimension(image=avatar, max_dimensions=(400, 400))
        return updated_avatar


class TestLoginForm(TestCase):
    def test_extra_fields(self):
        form = CustomLoginForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestPasswordResetForm(SimpleTestCase):
    def test_extra_fields(self):
        form = CustomPasswordResetForm()
        self.assertEqual(list(form.extra_fields), [("captcha", form["captcha"])])


class TestAvatarPreferenceForm(TestCase):
    def create_image(self, dimension):
        image = Image.new("RGB", dimension, color=(255, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle([(0, 0), dimension], fill=(0, 0, 0))
        temp_buffer = BytesIO()
        temp_buffer.seek(0)
        image.save(temp_buffer, format="PNG")
        return InMemoryUploadedFile(
            name="test_image.png",
            field_name="ImageField",
            file=temp_buffer,
            size=temp_buffer.tell(),
            charset=None,
            content_type="image/png",
        )

    def get_image_dimension(self, image):
        with Image.open(image) as f:
            return (f.width, f.height)

    def test_image_with_large_dimension_gets_reduced_to_default_avatar_preset(self):
        image = self.create_image(dimension=(800, 800))
        img_dimension = self.get_image_dimension(image)
        self.assertEqual(img_dimension, (800, 800))
        file = {"avatar": image}
        form = CustomAvatarPreferenceForm(files=file)
        self.assertTrue(form.is_valid())
        avatar = form.save()
        avatar_dimension = self.get_image_dimension(avatar)
        self.assertNotEqual(img_dimension, avatar_dimension)
        self.assertEqual(avatar_dimension, (400, 400))

    def test_image_with_lower_dimension_does_not_get_reduced_to_default_avatar_preset(
        self
    ):
        image = self.create_image(dimension=(400, 200))
        img_dimension = self.get_image_dimension(image)
        self.assertEqual(img_dimension, (400, 200))
        file = {"avatar": image}
        form = CustomAvatarPreferenceForm(files=file)
        self.assertTrue(form.is_valid())
        avatar = form.save()
        avatar_dimension = self.get_image_dimension(avatar)
        self.assertEqual(img_dimension, avatar_dimension)
        self.assertNotEqual(avatar_dimension, (400, 400))
