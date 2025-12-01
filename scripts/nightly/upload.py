import json
import pathlib
import sys
import uuid

import boto3

dist_folder = pathlib.Path.cwd() / "dist"

try:
    f = next(dist_folder.glob("*.whl"))
except StopIteration:
    print("No .whl files found in ./dist!")  # noqa: T201
    sys.exit()

print("Uploading", f.name)  # noqa: T201
s3 = boto3.client("s3")
s3.upload_file(
    str(f),
    "releases.wagtail.io",
    "nightly/dist/" + f.name,
)
# Redundant upload to a fixed filename for ease of use with package managers
print("Uploading latest.whl")  # noqa: T201
s3.upload_file(
    str(f),
    "releases.wagtail.io",
    "nightly/dist/latest.whl",
)

print("Updating latest.json")  # noqa: T201

boto3.resource("s3").Object("releases.wagtail.io", "nightly/latest.json").put(
    Body=json.dumps(
        {
            "url": "https://releases.wagtail.org/nightly/dist/" + f.name,
        }
    ),
)

print("Purging cache")  # noqa: T201

boto3.client("cloudfront").create_invalidation(
    DistributionId="E283SZ5CB4MDM0",
    InvalidationBatch={
        "Paths": {
            "Quantity": 2,
            "Items": ["/nightly/latest.json", "/nightly/dist/latest.whl"],
        },
        "CallerReference": str(uuid.uuid4()),
    },
)
