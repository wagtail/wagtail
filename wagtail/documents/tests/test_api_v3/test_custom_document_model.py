from unittest.mock import patch

from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from ninja import Schema

from wagtail.actions import CreateAction
from wagtail.api import APIField
from wagtail.api.v3.schemas import create_generator, patch_generator
from wagtail.documents.api.v3 import schemas as document_schemas
from wagtail.documents.api.v3.form_data import build_document_form
from wagtail.documents.forms import get_document_form
from wagtail.models import Collection, GroupCollectionPermission
from wagtail.test.testapp.models import CustomDocument
from wagtail.test.utils import WagtailTestUtils


@override_settings(WAGTAILDOCS_DOCUMENT_MODEL="tests.CustomDocument")
class TestV3CustomDocumentModel(WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_user(username="uploader", password="password")
        group = Group.objects.create(name="custom document uploaders")
        self.user.groups.add(group)
        permission = Permission.objects.get(
            content_type__app_label="wagtaildocs",
            codename="add_document",
        )
        GroupCollectionPermission.objects.create(
            group=group,
            collection=Collection.get_first_root_node(),
            permission=permission,
        )
        self.fields = [
            name
            for name in CustomDocument.admin_form_fields
            if name not in {"file", "tags"}
        ]

    def create_schema(self):
        return create_generator.generate_schema(
            CustomDocument,
            base_class=Schema,
            fields=self.fields,
            required_fields=("title",),
        )

    def test_create_schema_includes_custom_admin_form_fields(self):
        schema = self.create_schema()
        self.assertIn("description", schema.model_fields)
        self.assertIn("fancy_description", schema.model_fields)
        self.assertNotIn("file", schema.model_fields)
        self.assertNotIn("tags", schema.model_fields)

    def test_patch_schema_includes_custom_admin_form_fields(self):
        schema = patch_generator.generate_schema(
            CustomDocument,
            base_class=Schema,
            fields=self.fields,
        )
        self.assertIn("description", schema.model_fields)
        self.assertIn("fancy_description", schema.model_fields)
        self.assertTrue(
            all(not field.is_required() for field in schema.model_fields.values())
        )

    def test_document_input_schemas_include_writable_api_fields(self):
        admin_form_fields = tuple(
            field
            for field in CustomDocument.admin_form_fields
            if field not in {"file", "tags", "description"}
        )
        input_fields = [
            field for field in admin_form_fields if field not in {"file", "tags"}
        ]
        writable_api_fields = (
            APIField("file", writable=True),
            APIField("tags", writable=True),
            APIField("description", writable=True),
        )

        with (
            patch.object(CustomDocument, "admin_form_fields", admin_form_fields),
            patch.object(
                CustomDocument, "api_fields", writable_api_fields, create=True
            ),
            patch.object(document_schemas, "Document", CustomDocument),
            patch.object(document_schemas, "BASE_DOCUMENT_FIELDS", input_fields),
        ):
            _, create_schema, patch_schema = document_schemas.build_document_schemas()

        for schema in (create_schema, patch_schema):
            self.assertIn("fancy_description", schema.model_fields)
            self.assertIn("file", schema.model_fields)
            self.assertIn("tags", schema.model_fields)
            self.assertIn("description", schema.model_fields)

    def test_document_form_binds_custom_fields(self):
        form_class = get_document_form(CustomDocument)
        self.assertIn("description", form_class.base_fields)
        self.assertIn("fancy_description", form_class.base_fields)

    def test_create_action_saves_custom_document_and_metadata(self):
        data = self.create_schema().model_validate(
            {
                "title": "Custom",
                "description": "Plain description",
                "fancy_description": "<p>Fancy description</p>",
            }
        )
        form = build_document_form(
            CustomDocument,
            data,
            SimpleUploadedFile("custom.txt", b"Custom contents"),
            self.user,
        )
        self.assertFalse(form.errors)
        CreateAction(form.instance, user=self.user, form=form).execute()
        document = CustomDocument.objects.get(title="Custom")
        self.assertEqual(document.description, "Plain description")
        self.assertNotEqual(document.file_hash, "")
        self.assertEqual(document.file_size, len(b"Custom contents"))

    def test_custom_model_unique_constraint_returns_form_error(self):
        collection = Collection.get_first_root_node()
        CustomDocument.objects.create(
            title="Duplicate",
            file=SimpleUploadedFile("first.txt", b"First"),
            collection=collection,
        )
        data = self.create_schema().model_validate({"title": "Duplicate"})
        form = build_document_form(
            CustomDocument,
            data,
            SimpleUploadedFile("second.txt", b"Second"),
            self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    @override_settings(
        WAGTAILDOCS_DOCUMENT_FORM_BASE=(
            "wagtail.test.testapp.media_forms.AlternateDocumentForm"
        )
    )
    def test_configured_base_form_validation_is_used(self):
        data = self.create_schema().model_validate({"title": "Custom form"})
        form = build_document_form(
            CustomDocument,
            data,
            SimpleUploadedFile("custom-form.txt", b"Custom form contents"),
            self.user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("form_only_field", form.errors)
