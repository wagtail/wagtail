from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``id_ID`` locale."""

    license_formats = (
        "? ### ??",
        "? ### ???",
        "?? ### ??",
        "?? ### ???",
        "? #### ??",
        "? #### ???",
        "?? #### ??",
        "?? #### ???",
    )
