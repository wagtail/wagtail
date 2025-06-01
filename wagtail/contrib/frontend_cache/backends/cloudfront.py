import logging
import uuid
from collections import defaultdict
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import BaseBackend

logger = logging.getLogger("wagtail.frontendcache")


__all__ = ["CloudfrontBackend"]


class CloudfrontBackend(BaseBackend):
    def __init__(self, params):
        import boto3

        super().__init__(params)

        self.client = boto3.client(
            "cloudfront",
            aws_access_key_id=params.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=params.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=params.get("AWS_SESSION_TOKEN"),
        )

        try:
            self.cloudfront_distribution_id = params.pop("DISTRIBUTION_ID")
        except KeyError:
            raise ImproperlyConfigured(
                "The setting 'WAGTAILFRONTENDCACHE' requires the object 'DISTRIBUTION_ID'."
            )

    def purge_batch(self, urls):
        paths_by_distribution_id = defaultdict(set)

        for url in urls:
            url_parsed = urlparse(url)
            distribution_id = self.cloudfront_distribution_id

            if distribution_id:
                path = url_parsed.path or "/"
                if url_parsed.query:
                    path += "?" + url_parsed.query
                # Only append if the path is not already in the list
                if path not in paths_by_distribution_id[distribution_id]:
                    paths_by_distribution_id[distribution_id].add(path)

        for distribution_id, paths in paths_by_distribution_id.items():
            self._create_invalidation(distribution_id, list(paths))

    def purge(self, url):
        self.purge_batch([url])

    def _create_invalidation(self, distribution_id, paths):
        import botocore

        try:
            self.client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {"Quantity": len(paths), "Items": paths},
                    "CallerReference": str(uuid.uuid4()),
                },
            )
        except botocore.exceptions.ClientError as e:
            for path in paths:
                logger.error(
                    "Couldn't purge path '%s' from CloudFront (DistributionId=%s). ClientError: %s %s",
                    path,
                    distribution_id,
                    e.response["Error"]["Code"],
                    e.response["Error"]["Message"],
                )
