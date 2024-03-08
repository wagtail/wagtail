from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for `nl_BE` locale.

    https://nl.wikipedia.org/wiki/Belgisch_kenteken
    """

    license_formats = (
        "???-###",  # 1973-2008
        "###-???",  # 2008-2010
        # New formats after 2010
        "1-???-###",
        "2-???-###",
    )
