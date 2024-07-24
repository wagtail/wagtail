"""Different miscellaneous helper functions.

Mostly for internal use, so prototypes can change between versions.
"""

import builtins
import re
from dataclasses import dataclass
from enum import IntEnum
from math import ceil
from pathlib import Path
from struct import pack, unpack
from typing import List, Optional, Union

from PIL import Image

from . import options
from .constants import HeifChannel, HeifChroma, HeifColorspace, HeifCompressionFormat

try:
    import _pillow_heif
except ImportError as ex:
    from ._deffered_error import DeferredError

    _pillow_heif = DeferredError(ex)


MODE_INFO = {
    # name -> [channels, bits per pixel channel, colorspace, chroma]
    "BGRA;16": (4, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGRa;16": (4, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGR;16": (3, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "RGBA;16": (4, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGBa;16": (4, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGB;16": (3, 16, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "LA;16": (2, 16, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "La;16": (2, 16, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "L;16": (1, 16, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;16": (1, 16, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;16L": (1, 16, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "BGRA;12": (4, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGRa;12": (4, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGR;12": (3, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "RGBA;12": (4, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGBa;12": (4, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGB;12": (3, 12, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "LA;12": (2, 12, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "La;12": (2, 12, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "L;12": (1, 12, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;12": (1, 12, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;12L": (1, 12, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "BGRA;10": (4, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGRa;10": (4, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "BGR;10": (3, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "RGBA;10": (4, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGBa;10": (4, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBBAA_LE),
    "RGB;10": (3, 10, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RRGGBB_LE),
    "LA;10": (2, 10, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "La;10": (2, 10, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "L;10": (1, 10, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;10": (1, 10, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "I;10L": (1, 10, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "RGBA": (4, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGBA),
    "RGBa": (4, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGBA),
    "RGB": (3, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGB),
    "BGRA": (4, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGBA),
    "BGRa": (4, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGBA),
    "BGR": (3, 8, HeifColorspace.RGB, HeifChroma.INTERLEAVED_RGB),
    "LA": (2, 8, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "La": (2, 8, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "L": (1, 8, HeifColorspace.MONOCHROME, HeifChroma.MONOCHROME),
    "YCbCr": (3, 8, HeifColorspace.YCBCR, HeifChroma.CHROMA_444),
}

SUBSAMPLING_CHROMA_MAP = {
    "4:4:4": 444,
    "4:2:2": 422,
    "4:2:0": 420,
}

LIBHEIF_CHROMA_MAP = {
    1: 420,
    2: 422,
    3: 444,
}


def save_colorspace_chroma(c_image, info: dict) -> None:
    """Converts `chroma` value from `c_image` to useful values and stores them in ``info`` dict."""
    # Saving of `colorspace` was removed, as currently is not clear where to use that value.
    chroma = LIBHEIF_CHROMA_MAP.get(c_image.chroma, None)
    if chroma is not None:
        info["chroma"] = chroma


def set_orientation(info: dict) -> Optional[int]:
    """Reset orientation in ``EXIF`` to ``1`` if any orientation present.

    Removes ``XMP`` orientation tag if it is present.
    In Pillow plugin mode, it is called automatically for images.
    When ``pillow_heif`` used in ``standalone`` mode, if you wish, you can call it manually.

    .. note:: If there is no orientation tag, this function will not add it and do nothing.

        If both XMP and EXIF orientation tags are present, EXIF orientation tag will be returned,
        but both tags will be removed.

    :param info: `info` dictionary from :external:py:class:`~PIL.Image.Image` or :py:class:`~pillow_heif.HeifImage`.
    :returns: Original orientation or None if it is absent.
    """
    return _get_orientation(info, True)


def _get_orientation_for_encoder(info: dict) -> int:
    image_orientation = _get_orientation(info, False)
    return 1 if image_orientation is None else image_orientation


def _get_orientation_xmp(info: dict, exif_orientation: Optional[int], reset: bool = False) -> Optional[int]:
    xmp_orientation = 1
    if info.get("xmp"):
        xmp_data = info["xmp"].rsplit(b"\x00", 1)
        if xmp_data[0]:
            decoded_xmp_data = None
            for encoding in ("utf-8", "latin1"):
                try:
                    decoded_xmp_data = xmp_data[0].decode(encoding)
                    break
                except Exception:  # noqa # pylint: disable=broad-except
                    pass
            if decoded_xmp_data:
                match = re.search(r'tiff:Orientation(="|>)([0-9])', decoded_xmp_data)
                if match:
                    xmp_orientation = int(match[2])
                    if reset:
                        decoded_xmp_data = re.sub(r'tiff:Orientation="([0-9])"', "", decoded_xmp_data)
                        decoded_xmp_data = re.sub(r"<tiff:Orientation>([0-9])</tiff:Orientation>", "", decoded_xmp_data)
                # should encode in "utf-8" anyway, as `defusedxml` do not work with `latin1` encoding.
                if encoding != "utf-8" or xmp_orientation != 1:
                    info["xmp"] = b"".join([decoded_xmp_data.encode("utf-8"), b"\x00" if len(xmp_data) > 1 else b""])
    return xmp_orientation if exif_orientation is None and xmp_orientation != 1 else None


def _get_orientation(info: dict, reset: bool = False) -> Optional[int]:
    original_orientation = None
    if info.get("exif"):
        try:
            tif_tag = info["exif"]
            skipped_exif00 = False
            if tif_tag.startswith(b"Exif\x00\x00"):
                skipped_exif00 = True
                tif_tag = tif_tag[6:]
            endian_mark = "<" if tif_tag[0:2] == b"\x49\x49" else ">"
            pointer = unpack(endian_mark + "L", tif_tag[4:8])[0]
            tag_count = unpack(endian_mark + "H", tif_tag[pointer : pointer + 2])[0]
            offset = pointer + 2
            for tag_n in range(tag_count):
                pointer = offset + 12 * tag_n
                if unpack(endian_mark + "H", tif_tag[pointer : pointer + 2])[0] != 274:
                    continue
                value = tif_tag[pointer + 8 : pointer + 12]
                _original_orientation = unpack(endian_mark + "H", value[0:2])[0]
                if _original_orientation != 1:
                    original_orientation = _original_orientation
                    if not reset:
                        break
                    p_value = pointer + 8
                    if skipped_exif00:
                        p_value += 6
                    new_orientation = pack(endian_mark + "H", 1)
                    info["exif"] = info["exif"][:p_value] + new_orientation + info["exif"][p_value + 2 :]
                    break
        except Exception:  # noqa # pylint: disable=broad-except
            pass
    xmp_orientation = _get_orientation_xmp(info, original_orientation, reset=reset)
    return xmp_orientation if xmp_orientation else original_orientation


def get_file_mimetype(fp) -> str:
    """Gets the MIME type of the HEIF(or AVIF) object.

    :param fp: A filename (string), pathlib.Path object, file object or bytes.
        The file object must implement ``file.read``, ``file.seek`` and ``file.tell`` methods,
        and be opened in binary mode.
    :returns: "image/heic", "image/heif", "image/heic-sequence", "image/heif-sequence",
        "image/avif", "image/avif-sequence" or "".
    """
    heif_brand = _get_bytes(fp, 12)[8:]
    if heif_brand:
        if heif_brand == b"avif":
            return "image/avif"
        if heif_brand == b"avis":
            return "image/avif-sequence"
        if heif_brand in (b"heic", b"heix", b"heim", b"heis"):
            return "image/heic"
        if heif_brand in (b"hevc", b"hevx", b"hevm", b"hevs"):
            return "image/heic-sequence"
        if heif_brand == b"mif1":
            return "image/heif"
        if heif_brand == b"msf1":
            return "image/heif-sequence"
    return ""


def _get_bytes(fp, length=None) -> bytes:
    if isinstance(fp, (str, Path)):
        with builtins.open(fp, "rb") as file:
            return file.read(length or -1)
    if hasattr(fp, "read"):
        offset = fp.tell() if hasattr(fp, "tell") else None
        result = fp.read(length or -1)
        if offset is not None and hasattr(fp, "seek"):
            fp.seek(offset)
        return result
    return bytes(fp)[:length]


def _retrieve_exif(metadata: List[dict]) -> Optional[bytes]:
    _result = None
    _purge = []
    for i, md_block in enumerate(metadata):
        if md_block["type"] == "Exif":
            _purge.append(i)
            skip_size = int.from_bytes(md_block["data"][:4], byteorder="big", signed=False)
            skip_size += 4  # skip 4 bytes with offset
            if len(md_block["data"]) - skip_size <= 4:  # bad EXIF data, skip first 4 bytes
                skip_size = 4
            elif skip_size >= 6 and md_block["data"][skip_size - 6 : skip_size] == b"Exif\x00\x00":
                skip_size -= 6
            _data = md_block["data"][skip_size:]
            if not _result and _data:
                _result = _data
    for i in reversed(_purge):
        del metadata[i]
    return _result


def _retrieve_xmp(metadata: List[dict]) -> Optional[bytes]:
    _result = None
    _purge = []
    for i, md_block in enumerate(metadata):
        if md_block["type"] == "mime":
            _purge.append(i)
            if not _result:
                _result = md_block["data"]
    for i in reversed(_purge):
        del metadata[i]
    return _result


def _exif_from_pillow(img: Image.Image) -> Optional[bytes]:
    if "exif" in img.info:
        return img.info["exif"]
    if hasattr(img, "getexif"):  # noqa
        exif = img.getexif()
        if exif:
            return exif.tobytes()
    return None


def _xmp_from_pillow(img: Image.Image) -> Optional[bytes]:
    _xmp = None
    if "xmp" in img.info:
        _xmp = img.info["xmp"]
    elif "XML:com.adobe.xmp" in img.info:  # PNG
        _xmp = img.info["XML:com.adobe.xmp"]
    elif hasattr(img, "tag_v2"):  # TIFF
        if 700 in img.tag_v2:
            _xmp = img.tag_v2[700]
    elif hasattr(img, "applist"):  # JPEG
        for segment, content in img.applist:
            if segment == "APP1":
                marker, xmp_tags = content.rsplit(b"\x00", 1)
                if marker == b"http://ns.adobe.com/xap/1.0/":
                    _xmp = xmp_tags
                    break
    if isinstance(_xmp, str):
        _xmp = _xmp.encode("utf-8")
    return _xmp


def _pil_to_supported_mode(img: Image.Image) -> Image.Image:
    # We support "YCbCr" for encoding in Pillow plugin mode and do not call this function.
    if img.mode == "P":
        mode = "RGBA" if img.info.get("transparency") else "RGB"
        img = img.convert(mode=mode)
    elif img.mode == "I":
        img = img.convert(mode="I;16L")
    elif img.mode == "1":
        img = img.convert(mode="L")
    elif img.mode == "CMYK":
        img = img.convert(mode="RGBA")
    elif img.mode == "YCbCr":
        img = img.convert(mode="RGB")
    return img


class Transpose(IntEnum):
    """Temporary workaround till we support old Pillows, remove this when a minimum Pillow version will have this."""

    FLIP_LEFT_RIGHT = 0
    FLIP_TOP_BOTTOM = 1
    ROTATE_90 = 2
    ROTATE_180 = 3
    ROTATE_270 = 4
    TRANSPOSE = 5
    TRANSVERSE = 6


def _rotate_pil(img: Image.Image, orientation: int) -> Image.Image:
    # Probably need create issue in Pillow to add support
    # for info["xmp"] or `getxmp()` for ImageOps.exif_transpose and remove this func.
    method = {
        2: Transpose.FLIP_LEFT_RIGHT,
        3: Transpose.ROTATE_180,
        4: Transpose.FLIP_TOP_BOTTOM,
        5: Transpose.TRANSPOSE,
        6: Transpose.ROTATE_270,
        7: Transpose.TRANSVERSE,
        8: Transpose.ROTATE_90,
    }.get(orientation)
    if method is not None:
        return img.transpose(method)
    return img


def _get_primary_index(some_iterator, primary_index: Optional[int]) -> int:
    primary_attrs = [_.info.get("primary", False) for _ in some_iterator]
    if primary_index is None:
        primary_index = 0
        for i, v in enumerate(primary_attrs):
            if v:
                primary_index = i
    elif primary_index == -1 or primary_index >= len(primary_attrs):
        primary_index = len(primary_attrs) - 1
    return primary_index


class CtxEncode:
    """Encoder bindings from python to python C module."""

    def __init__(self, compression_format: HeifCompressionFormat, **kwargs):
        quality = kwargs.get("quality", options.QUALITY)
        self.ctx_write = _pillow_heif.CtxWrite(
            compression_format,
            -2 if quality is None else quality,
            options.PREFERRED_ENCODER.get("HEIF" if compression_format == HeifCompressionFormat.HEVC else "AVIF", ""),
        )
        enc_params = kwargs.get("enc_params", {})
        chroma = None
        if "subsampling" in kwargs:
            chroma = SUBSAMPLING_CHROMA_MAP.get(kwargs["subsampling"], None)
        if chroma is None:
            chroma = kwargs.get("chroma", None)
        if chroma:
            enc_params["chroma"] = chroma
        for key, value in enc_params.items():
            _value = value if isinstance(value, str) else str(value)
            self.ctx_write.set_parameter(key, _value)

    def add_image(self, size: tuple, mode: str, data, **kwargs) -> None:
        """Adds image to the encoder."""
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError("Empty images are not supported.")
        bit_depth_in = MODE_INFO[mode][1]
        bit_depth_out = 8 if bit_depth_in == 8 else kwargs.get("bit_depth", 16)
        if bit_depth_out == 16:
            bit_depth_out = 12 if options.SAVE_HDR_TO_12_BIT else 10
        premultiplied_alpha = int(mode.split(sep=";")[0][-1] == "a")
        # creating image
        im_out = self.ctx_write.create_image(size, MODE_INFO[mode][2], MODE_INFO[mode][3], premultiplied_alpha)
        # image data
        if MODE_INFO[mode][0] == 1:
            im_out.add_plane_l(size, bit_depth_out, bit_depth_in, data, kwargs.get("stride", 0), HeifChannel.CHANNEL_Y)
        elif MODE_INFO[mode][0] == 2:
            im_out.add_plane_la(size, bit_depth_out, bit_depth_in, data, kwargs.get("stride", 0))
        else:
            im_out.add_plane(size, bit_depth_out, bit_depth_in, data, mode.find("BGR") != -1, kwargs.get("stride", 0))
        self._finish_add_image(im_out, size, **kwargs)

    def add_image_ycbcr(self, img: Image.Image, **kwargs) -> None:
        """Adds image in `YCbCR` mode to the encoder."""
        # creating image
        im_out = self.ctx_write.create_image(img.size, MODE_INFO[img.mode][2], MODE_INFO[img.mode][3], 0)
        # image data
        for i in (HeifChannel.CHANNEL_Y, HeifChannel.CHANNEL_CB, HeifChannel.CHANNEL_CR):
            im_out.add_plane_l(img.size, 8, 8, bytes(img.getdata(i)), kwargs.get("stride", 0), i)
        self._finish_add_image(im_out, img.size, **kwargs)

    def _finish_add_image(self, im_out, size: tuple, **kwargs):
        # set ICC color profile
        __icc_profile = kwargs.get("icc_profile", None)
        if __icc_profile is not None:
            im_out.set_icc_profile(kwargs.get("icc_profile_type", "prof"), __icc_profile)
        # set NCLX color profile
        if kwargs.get("nclx_profile", None):
            im_out.set_nclx_profile(
                *[
                    kwargs["nclx_profile"][i]
                    for i in ("color_primaries", "transfer_characteristics", "matrix_coefficients", "full_range_flag")
                ]
            )
        # encode
        image_orientation = kwargs.get("image_orientation", 1)
        im_out.encode(
            self.ctx_write,
            kwargs.get("primary", False),
            kwargs.get("save_nclx_profile", options.SAVE_NCLX_PROFILE),
            kwargs.get("color_primaries", -1),
            kwargs.get("transfer_characteristics", -1),
            kwargs.get("matrix_coefficients", -1),
            kwargs.get("full_range_flag", -1),
            image_orientation,
        )
        # adding metadata
        exif = kwargs.get("exif", None)
        if exif is not None:
            if isinstance(exif, Image.Exif):
                exif = exif.tobytes()
            im_out.set_exif(self.ctx_write, exif)
        xmp = kwargs.get("xmp", None)
        if xmp is not None:
            im_out.set_xmp(self.ctx_write, xmp)
        for metadata in kwargs.get("metadata", []):
            im_out.set_metadata(self.ctx_write, metadata["type"], metadata["content_type"], metadata["data"])
        # adding thumbnails
        for thumb_box in kwargs.get("thumbnails", []):
            if max(size) > thumb_box > 3:
                im_out.encode_thumbnail(self.ctx_write, thumb_box, image_orientation)

    def save(self, fp) -> None:
        """Ask encoder to produce output based on previously added images."""
        data = self.ctx_write.finalize()
        if isinstance(fp, (str, Path)):
            with builtins.open(fp, "wb") as f:
                f.write(data)
        elif hasattr(fp, "write"):
            fp.write(data)
        else:
            raise TypeError("`fp` must be a path to file or an object with `write` method.")


@dataclass
class MimCImage:
    """Mimicry of the HeifImage class."""

    def __init__(self, mode: str, size: tuple, data: bytes, **kwargs):
        self.mode = mode
        self.size = size
        self.stride: int = kwargs.get("stride", size[0] * MODE_INFO[mode][0] * ceil(MODE_INFO[mode][1] / 8))
        self.data = data
        self.metadata: List[dict] = []
        self.color_profile = None
        self.thumbnails: List[int] = []
        self.depth_image_list: List = []
        self.primary = False
        self.chroma = HeifChroma.UNDEFINED.value
        self.colorspace = HeifColorspace.UNDEFINED.value

    @property
    def size_mode(self):
        """Mimicry of c_image property."""
        return self.size, self.mode

    @property
    def bit_depth(self) -> int:
        """Return bit-depth based on image mode."""
        return MODE_INFO[self.mode][1]


def load_libheif_plugin(plugin_path: Union[str, Path]) -> None:
    """Load specified LibHeif plugin."""
    _pillow_heif.load_plugin(plugin_path)
