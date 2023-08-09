import logging
from typing import Iterable, Set, Tuple

from django.conf import settings
from django.db.models import Q

from wagtail.coreutils import BatchCreator, get_dummy_request
from wagtail.models import Page, Site

from .models import Redirect

logger = logging.getLogger(__name__)


class BatchRedirectCreator(BatchCreator):
    """
    A specialized ``BatchCreator`` class for saving ``Redirect`` objects.
    """

    model = Redirect

    def pre_process(self):
        # delete any existing automatically-created redirects that might clash
        # with the items in `self.items`
        clashes_q = Q()
        for item in self.items:
            clashes_q |= Q(old_path=item.old_path, site_id=item.site_id)
        Redirect.objects.filter(automatically_created=True).filter(clashes_q).delete()


def autocreate_redirects_on_slug_change(
    instance_before: Page, instance: Page, **kwargs
):
    # NB: `page_slug_changed` provides specific page instances,
    # so we do not need to 'upcast' them for create_redirects here

    if not getattr(settings, "WAGTAILREDIRECTS_AUTO_CREATE", True):
        return None

    # Determine sites to create redirects for
    sites = Site.objects.filter(
        id__in=[
            option.site_id
            for option in instance._get_relevant_site_root_paths(cache_object=instance)
        ]
    ).exclude(root_page=instance)

    create_redirects(page=instance, page_old=instance_before, sites=sites)


def autocreate_redirects_on_page_move(
    instance: Page,
    url_path_after: str,
    url_path_before: str,
    **kwargs,
) -> None:
    if not getattr(settings, "WAGTAILREDIRECTS_AUTO_CREATE", True):
        return None

    if url_path_after == url_path_before:
        # Redirects are not needed for a page 'reorder'
        return None

    # NB: create_redirects expects specific instances
    instance = instance.specific

    # Simulate an 'old_page' by copying the specific instance and resetting
    # the in-memory `url_path` value to what it was before the move
    page_old = type(instance)()
    page_old.__dict__.update(instance.__dict__)
    page_old.url_path = url_path_before

    # This value is used to prevent creation redirects that link
    # from one site to another
    new_site_ids = {
        item.site_id
        for item in instance._get_relevant_site_root_paths(cache_object=instance)
    }

    # Determine sites to create redirects for
    sites = Site.objects.exclude(root_page=instance).filter(
        id__in=[
            item.site_id
            for item in page_old._get_relevant_site_root_paths(cache_object=instance)
            if item.site_id in new_site_ids
        ]
    )
    create_redirects(page=instance, page_old=page_old, sites=sites)


def _page_urls_for_sites(
    page: Page, sites: Tuple[Site], cache_target: Page
) -> Set[Tuple[Site, str, str]]:
    urls = set()
    for site in sites:

        # use a `HttpRequest` to influence the return value
        request = get_dummy_request(site=site)
        # reuse cached site root paths if available
        if hasattr(cache_target, "_wagtail_cached_site_root_paths"):
            request._wagtail_cached_site_root_paths = (
                cache_target._wagtail_cached_site_root_paths
            )

        url_parts = page.get_url_parts(request)
        if url_parts is None:
            continue
        site_id, root_url, page_path = url_parts

        if page_path:
            for route_path in page.get_route_paths():
                normalized_route_path = Redirect.normalise_page_route_path(route_path)
                old_path = Redirect.normalise_path(
                    page_path.rstrip("/") + (normalized_route_path or "/")
                )
                urls.add((site, old_path, normalized_route_path))

        # copy cached site root paths to `cache_target` to retain benefits
        cache_target._wagtail_cached_site_root_paths = (
            request._wagtail_cached_site_root_paths
        )

    return urls


def create_redirects(page: Page, page_old: Page, sites: Iterable[Site]) -> None:
    url_path_length = len(page.url_path)
    sites = tuple(sites)

    if not sites:
        return None

    logger.info(f"Creating redirects for page: '{page}' id={page.id}")

    # For bulk-creating redirects in batches
    batch = BatchRedirectCreator(max_size=2000, ignore_conflicts=True)

    # Treat the page that was updated / moved separately to it's decendants,
    # because there may be changes to fields other than `slug` or `url_path`
    # that impact the URL.
    old_urls = _page_urls_for_sites(page_old, sites, cache_target=page)
    new_urls = _page_urls_for_sites(page, sites, cache_target=page)

    # Add redirects for urls that have changed
    changed_urls = old_urls - new_urls
    for site, old_path, route_path in changed_urls:
        batch.add(
            old_path=old_path,
            site=site,
            redirect_page=page,
            redirect_page_route_path=route_path,
            automatically_created=True,
        )

    # Now, repeat the process for each descendant page.
    # Only the `url_path` value of descendants should have been affected by the
    # change, so we can use in-memory manipulation of `url_path` to figure out what
    # the old URLS were

    for descendant in (
        page.get_descendants().live().defer_streamfields().specific().iterator()
    ):
        new_urls = _page_urls_for_sites(descendant, sites, cache_target=page)

        # Restore old 'url_path' value on in-memory instance
        descendant.url_path = page_old.url_path + descendant.url_path[url_path_length:]

        old_urls = _page_urls_for_sites(descendant, sites, cache_target=page)

        # Add redirects for urls that have changed
        changed_urls = old_urls - new_urls
        for site, old_path, route_path in changed_urls:
            batch.add(
                old_path=old_path,
                site=site,
                redirect_page=descendant,
                redirect_page_route_path=route_path,
                automatically_created=True,
            )

    # Process the final batch
    batch.process()
    logger.info(batch.get_summary())
