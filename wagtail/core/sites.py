from django.apps import apps
from django.db.models import Case, IntegerField, Q, When

MATCH_HOSTNAME_PORT = 0
MATCH_HOSTNAME_DEFAULT = 1
MATCH_DEFAULT = 2
MATCH_HOSTNAME = 3


def get_site_for_hostname(hostname, port):
    """Return the wagtailcore.Site object for the given hostname and port."""
    Site = apps.get_model('wagtailcore.Site')

    sites = list(Site.objects.annotate(match=Case(
        # annotate the results by best choice descending

        # put exact hostname+port match first
        When(hostname=hostname, port=port, then=MATCH_HOSTNAME_PORT),

        # then put hostname+default (better than just hostname or just default)
        When(hostname=hostname, is_default_site=True, then=MATCH_HOSTNAME_DEFAULT),

        # then match default with different hostname. there is only ever
        # one default, so order it above (possibly multiple) hostname
        # matches so we can use sites[0] below to access it
        When(is_default_site=True, then=MATCH_DEFAULT),

        # because of the filter below, if it's not default then its a hostname match
        default=MATCH_HOSTNAME,

        output_field=IntegerField(),
    )).filter(Q(hostname=hostname) | Q(is_default_site=True)).order_by(
        'match'
    ).select_related(
        'root_page'
    ))

    if sites:
        # if theres a unique match or hostname (with port or default) match
        if len(sites) == 1 or sites[0].match in (MATCH_HOSTNAME_PORT, MATCH_HOSTNAME_DEFAULT):
            return sites[0]

        # if there is a default match with a different hostname, see if
        # there are many hostname matches. if only 1 then use that instead
        # otherwise we use the default
        if sites[0].match == MATCH_DEFAULT:
            return sites[len(sites) == 2]

    raise Site.DoesNotExist()
