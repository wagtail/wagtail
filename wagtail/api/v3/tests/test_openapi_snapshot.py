import json
from pathlib import Path

import swapper
from ninja.responses import NinjaJSONEncoder

from wagtail.api.v3.api import api
from wagtail.api.v3.tests.base import TestV3Base

if swapper.is_swapped("wagtailcore", "Page"):
    SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "openapi_basepage.json"
else:
    SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "openapi.json"


class TestOpenAPISnapshot(TestV3Base):
    def test_openapi_version(self):
        schema = api.get_openapi_schema()
        self.assertEqual(schema["openapi"], "3.1.0")

    def test_documents_contract(self):
        schema = api.get_openapi_schema()
        paths = schema["paths"]

        self.assertEqual(
            set(paths["/api/v3/documents/"]),
            {"get", "post"},
        )
        self.assertEqual(
            set(paths["/api/v3/documents/{document_id}/"]),
            {"get", "patch", "delete"},
        )

        operations = {
            paths["/api/v3/documents/"]["get"]["operationId"],
            paths["/api/v3/documents/"]["post"]["operationId"],
            paths["/api/v3/documents/{document_id}/"]["get"]["operationId"],
            paths["/api/v3/documents/{document_id}/"]["patch"]["operationId"],
            paths["/api/v3/documents/{document_id}/"]["delete"]["operationId"],
        }
        self.assertEqual(
            operations,
            {
                "documents_list",
                "documents_detail",
                "documents_create",
                "documents_update",
                "documents_delete",
            },
        )

        post_content = paths["/api/v3/documents/"]["post"]["requestBody"]["content"]
        self.assertEqual(set(post_content), {"multipart/form-data"})
        multipart_schema = post_content["multipart/form-data"]["schema"]
        self.assertEqual(set(multipart_schema["required"]), {"file", "title"})
        self.assertEqual(
            multipart_schema["properties"]["file"],
            {"format": "binary", "title": "File", "type": "string"},
        )
        self.assertNotIn("tags", multipart_schema["properties"])

        patch_content = paths["/api/v3/documents/{document_id}/"]["patch"][
            "requestBody"
        ]["content"]
        self.assertEqual(set(patch_content), {"application/json"})
        patch_schema = schema["components"]["schemas"]["DocumentPatchSchema"]
        self.assertNotIn("file", patch_schema["properties"])
        self.assertNotIn("tags", patch_schema["properties"])

    def test_openapi_schema_matches_snapshot(self):
        schema = api.get_openapi_schema()
        if not SNAPSHOT_PATH.exists():
            self.fail(
                f"OpenAPI snapshot missing at {SNAPSHOT_PATH}. "
                "Regenerate with the commands in the contributing docs."
            )

        with open(SNAPSHOT_PATH) as f:
            expected = json.load(f)

        actual = json.loads(json.dumps(schema, cls=NinjaJSONEncoder, sort_keys=True))
        self.assertEqual(actual, expected)
