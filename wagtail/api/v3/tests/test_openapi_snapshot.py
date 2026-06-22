import json
from pathlib import Path

from django.test import SimpleTestCase
from ninja.responses import NinjaJSONEncoder

from wagtail.api.v3.api import api

SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "openapi.json"


class TestOpenAPISnapshot(SimpleTestCase):
    def test_openapi_version(self):
        schema = api.get_openapi_schema()
        self.assertEqual(schema["openapi"], "3.1.0")

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
