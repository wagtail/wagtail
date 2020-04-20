import datetime
import pathlib
import sys
import json

import boto3

dist_folder = pathlib.Path.cwd() / 'dist'

try:
    f = next(dist_folder.glob('*.whl'))
except StopIteration:
    print("No .whl files found in ./dist!")
    sys.exit()

print("Uploading", f.name)
s3 = boto3.client('s3')
s3.upload_file(str(f), 'releases.wagtail.io', 'nightly/dist/' + f.name, ExtraArgs={'ACL':'public-read'})

print("Updating latest.json")

boto3.resource('s3').Object('releases.wagtail.io', 'nightly/latest.json').put(
    ACL='public-read',
    Body=json.dumps({
        "url": 'https://releases.wagtail.io/nightly/dist/' + f.name,
    })
)
