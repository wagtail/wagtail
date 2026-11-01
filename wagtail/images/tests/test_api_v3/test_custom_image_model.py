from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from ninja import Schema

from wagtail.api.v3.schemas import create_generator, patch_generator, read_generator
from wagtail.api.v3.schemas.base import BaseSchema
from wagtail.images.api.v3.form_data import build_image_form
from wagtail.images.forms import get_image_form
from wagtail.models import Collection, GroupCollectionPermission
from wagtail.test.testapp.models import CustomImage
from wagtail.test.utils import WagtailTestUtils


@override_settings(WAGTAILIMAGES_IMAGE_MODEL="tests.CustomImage")
class TestV3CustomImageModel(WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        # A user with add permission in a collection, so the image form's
        # collection choices can construct (BaseCollectionMemberForm raises
        # for users with no collection permissions).
        self.user = self.create_user(username="uploader", password="password")
        group = Group.objects.create(name="uploaders")
        self.user.groups.add(group)
        add_permission = Permission.objects.get(
            content_type__app_label="wagtailimages", codename="add_image"
        )
        GroupCollectionPermission.objects.create(
            group=group,
            collection=Collection.get_first_root_node(),
            permission=add_permission,
        )

    def test_read_schema_includes_custom_api_fields(self):
        read_schema = read_generator.generate_schema(CustomImage, base_class=BaseSchema)
        # No api_fields on CustomImage in the test app; the read schema is the
        # minimal base. Custom writable fields are covered by the form path.
        self.assertIn("meta", read_schema.model_fields)

    def test_create_schema_includes_custom_admin_form_fields(self):
        fields = [
            name
            for name in CustomImage.admin_form_fields
            if name not in {"file", "tags"}
        ]
        create_schema = create_generator.generate_schema(
            CustomImage, base_class=Schema, fields=fields, required_fields=("title",)
        )
        properties = create_schema.model_json_schema()["properties"]
        self.assertIn("caption", properties)
        self.assertIn("fancy_caption", properties)
        # Not editable in the admin -> not exposed.
        self.assertNotIn("not_editable_field", properties)

    def test_patch_schema_includes_custom_fields(self):
        fields = [
            name
            for name in CustomImage.admin_form_fields
            if name not in {"file", "tags"}
        ]
        patch_schema = patch_generator.generate_schema(
            CustomImage, base_class=Schema, fields=fields
        )
        self.assertIn("caption", patch_schema.model_fields)

    def test_image_form_binds_custom_field(self):
        form_class = get_image_form(CustomImage)
        self.assertIn("caption", form_class.base_fields)
        self.assertIn("fancy_caption", form_class.base_fields)
        self.assertNotIn("not_editable_field", form_class.base_fields)

    def test_create_action_saves_custom_image(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from wagtail.actions import CreateAction
        from wagtail.images.tests.utils import get_test_image_file

        # Build a validated create-input schema instance for CustomImage.
        fields = [
            name
            for name in CustomImage.admin_form_fields
            if name not in {"file", "tags"}
        ]
        create_schema = create_generator.generate_schema(
            CustomImage, base_class=Schema, fields=fields, required_fields=("title",)
        )
        data = create_schema.model_validate({"title": "Custom", "caption": "A caption"})
        form = build_image_form(
            CustomImage,
            data,
            SimpleUploadedFile("test.png", get_test_image_file().file.getvalue()),
            user=self.user,
        )
        self.assertFalse(form.errors)
        action = CreateAction(form.instance, user=None, form=form)
        action.execute(skip_permission_checks=True)
        self.assertEqual(CustomImage.objects.get(title="Custom").caption, "A caption")
