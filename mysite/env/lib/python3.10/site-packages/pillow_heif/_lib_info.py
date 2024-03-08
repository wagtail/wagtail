"""Functions to get versions of underlying libraries."""

try:
    import _pillow_heif
except ImportError as ex:
    from ._deffered_error import DeferredError

    _pillow_heif = DeferredError(ex)


def libheif_version() -> str:
    """Returns ``libheif`` version."""
    return _pillow_heif.get_lib_info()["libheif"]


def libheif_info() -> dict:
    """Returns a dictionary with version information.

    The keys `libheif`, `HEIF`, `AVIF`, `encoders`, `decoders` are always present, but values for all except
    `libheif` can be empty.

    {
        'libheif': '1.15.2',
        'HEIF': 'x265 HEVC encoder (3.4+31-6722fce1f)',
        'AVIF': 'AOMedia Project AV1 Encoder 3.5.0',
        'encoders': {
            'encoder1_id': 'encoder1_full_name',
            'encoder2_id': 'encoder2_full_name',
        },
        'decoders': {
            'decoder1_id': 'decoder1_full_name',
            'decoder2_id': 'decoder2_full_name',
        },
    }
    """
    return _pillow_heif.get_lib_info()
