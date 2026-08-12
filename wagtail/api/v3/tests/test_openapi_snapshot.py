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
            "GET /api/v3/documents/": paths["/api/v3/documents/"]["get"]["operationId"],
            "POST /api/v3/documents/": paths["/api/v3/documents/"]["post"][
                "operationId"
            ],
            "GET /api/v3/documents/{document_id}/": paths[
                "/api/v3/documents/{document_id}/"
            ]["get"]["operationId"],
            "PATCH /api/v3/documents/{document_id}/": paths[
                "/api/v3/documents/{document_id}/"
            ]["patch"]["operationId"],
            "DELETE /api/v3/documents/{document_id}/": paths[
                "/api/v3/documents/{document_id}/"
            ]["delete"]["operationId"],
        }
        self.assertEqual(
            operations,
            {
                "GET /api/v3/documents/": "documents_list",
                "POST /api/v3/documents/": "documents_create",
                "GET /api/v3/documents/{document_id}/": "documents_detail",
                "PATCH /api/v3/documents/{document_id}/": "documents_update",
                "DELETE /api/v3/documents/{document_id}/": "documents_delete",
            },
        )

        optional_bearer_security = [{"BearerTokenAuth": []}, {}]
        bearer_security = [{"BearerTokenAuth": []}]
        self.assertEqual(
            paths["/api/v3/documents/"]["get"]["security"],
            optional_bearer_security,
        )
        self.assertEqual(
            paths["/api/v3/documents/{document_id}/"]["get"]["security"],
            optional_bearer_security,
        )
        self.assertEqual(
            paths["/api/v3/documents/"]["post"]["security"], bearer_security
        )
        self.assertEqual(
            paths["/api/v3/documents/{document_id}/"]["patch"]["security"],
            bearer_security,
        )
        self.assertEqual(
            paths["/api/v3/documents/{document_id}/"]["delete"]["security"],
            bearer_security,
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
