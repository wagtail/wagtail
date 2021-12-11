import logging

from typing import Optional

from django.conf import settings
from django.db.models import Q

from wagtail.core.models import BaseLogEntry, Page, PageBase
from wagtail.core.utils import BatchCreator, get_dummy_request

from .models import Redirect


logger = logging.getLogger(__name__)


class BatchRedirectCreator(BatchCreator):
    """
    A specialized ``BatchCreator`` class for saving ``Redirect`` objects.
    """

    model = Redirect

    def initialize_instance(self, kwargs):
        # Automatically normalise paths when creating instances from kwargs
        kwargs["old_path"] = Redirect.normalise_path(kwargs["old_path"])
        return super().initialize_instance(kwargs)

    def pre_process(self):
        # delete any existing automatically-created redirects that might clash
        # with the items in `self.items`
        clashes_q = Q()
        for item in self.items:
            clashes_q |= Q(old_path=item.old_path, site_id=item.site_id)
        Redirect.objects.filter(automatically_created=True).filter(clashes_q).delete()


def autocreate_redirects(
    sender: PageBase, instance: Page, url_path_before: str, url_path_after: str, log_entry: Optional[BaseLogEntry] = None
) -> None:
    if instance.is_site_root():
        # url_path changes for site root pages do not affect URLs generally,
        # so we can exit early here.
        return None

    logger.info(f"Creating redirects for page: '{instance}' id={instance.id}")
    batch = BatchRedirectCreator(
        max_size=getattr(settings, "WAGTAILREDIRECTS_AUTOCREATE_BATCH_SIZE", 2000),
        ignore_conflicts=True,
    )
    request = get_dummy_request()

    for page in (
        instance.get_descendants(inclusive=True)
        .live()
        .specific(defer=True)
        .iterator()
    ):
        try:
            new_site_id, _, new_url = page.get_url_parts(request)
        except TypeError:
            continue

        # Restore old 'url_path' value on in-memory instance
        new_path_length = len(url_path_after)
        original_url_path = page.url_path
        page.url_path = url_path_before + original_url_path[new_path_length:]
        try:
            # Use modified page to retrieve old site and url
            old_site_id, _, old_url = page.get_url_parts(request)
        except TypeError:
            continue

        if (old_site_id, old_url) != (new_site_id, new_url):
            page_paths = [old_url]
            page_paths.extend(
                old_url.rstrip("/") + path for path in page.get_cached_paths() if path != "/"
            )
            batch.extend(
                dict(
                    old_path=path,
                    site_id=old_site_id,
                    redirect_page=page,
                    automatically_created=True,
                    trigger=log_entry
                )
                for path in page_paths
            )

    # Process the final batch
    batch.process()
    logger.info(batch.get_summary())
