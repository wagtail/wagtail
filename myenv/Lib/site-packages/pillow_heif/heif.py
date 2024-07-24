"""Functions and classes for heif images to read and write."""

from copy import copy, deepcopy
from io import SEEK_SET
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from . import options
from .constants import HeifCompressionFormat
from .misc import (
    MODE_INFO,
    CtxEncode,
    MimCImage,
    _exif_from_pillow,
    _get_bytes,
    _get_orientation_for_encoder,
    _get_primary_index,
    _pil_to_supported_mode,
    _retrieve_exif,
    _retrieve_xmp,
    _rotate_pil,
    _xmp_from_pillow,
    get_file_mimetype,
    save_colorspace_chroma,
    set_orientation,
)

try:
    import _pillow_heif
except ImportError as ex:
    from ._deffered_error import DeferredError

    _pillow_heif = DeferredError(ex)


class BaseImage:
    """Base class for :py:class:`HeifImage` and :py:class:`HeifDepthImage`."""

    size: tuple
    """Width and height of the image."""

    mode: str
    """A string which defines the type and depth of a pixel in the image:
    `Pillow Modes <https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes>`_

    For currently supported modes by Pillow-Heif see :ref:`image-modes`."""

    def __init__(self, c_image):
        self.size, self.mode = c_image.size_mode
        self._c_image = c_image
        self._data = None

    @property
    def data(self):
        """Decodes image and returns image data.

        :returns: ``bytes`` of the decoded image.
        """
        self.load()
        return self._data

    @property
    def stride(self) -> int:
        """Stride of the image.

        .. note:: from `0.10.0` version this value always will have width * sizeof pixel in default usage mode.

        :returns: An Int value indicating the image stride after decoding.
        """
        self.load()
        return self._c_image.stride

    @property
    def __array_interface__(self):
        """Numpy array interface support."""
        self.load()
        width = int(self.stride / MODE_INFO[self.mode][0])
        if MODE_INFO[self.mode][1] <= 8:
            typestr = "|u1"
        else:
            width = int(width / 2)
            typestr = "<u2"
        shape: Tuple[Any, ...] = (self.size[1], width)
        if MODE_INFO[self.mode][0] > 1:
            shape += (MODE_INFO[self.mode][0],)
        return {"shape": shape, "typestr": typestr, "version": 3, "data": self.data}

    def to_pillow(self) -> Image.Image:
        """Helper method to create :external:py:class:`~PIL.Image.Image` class.

        :returns: :external:py:class:`~PIL.Image.Image` class created from an image.
        """
        self.load()
        return Image.frombytes(
            self.mode,  # noqa
            self.size,
            self.data,
            "raw",
            self.mode,
            self.stride,
        )

    def load(self) -> None:
        """Method to decode image.

        .. note:: In normal cases, you should not call this method directly,
            when reading `data` or `stride` property of image will be loaded automatically.
        """
        if not self._data:
            self._data = self._c_image.data
            self.size, _ = self._c_image.size_mode


class HeifDepthImage(BaseImage):
    """Class representing the depth image associated with the :py:class:`~pillow_heif.HeifImage` class."""

    def __init__(self, c_image):
        super().__init__(c_image)
        _metadata: dict = c_image.metadata
        self.info = {
            "metadata": _metadata,
        }
        save_colorspace_chroma(c_image, self.info)

    def __repr__(self):
        _bytes = f"{len(self.data)} bytes" if self._data or isinstance(self._c_image, MimCImage) else "no"
        return f"<{self.__class__.__name__} {self.size[0]}x{self.size[1]} {self.mode}>"

    def to_pillow(self) -> Image.Image:
        """Helper method to create :external:py:class:`~PIL.Image.Image` class.

        :returns: :external:py:class:`~PIL.Image.Image` class created from an image.
        """
        image = super().to_pillow()
        image.info = self.info.copy()
        return image


class HeifImage(BaseImage):
    """One image in a :py:class:`~pillow_heif.HeifFile` container."""

    def __init__(self, c_image):
        super().__init__(c_image)
        _metadata: List[dict] = c_image.metadata
        _exif = _retrieve_exif(_metadata)
        _xmp = _retrieve_xmp(_metadata)
        _thumbnails: List[Optional[int]] = (
            [i for i in c_image.thumbnails if i is not None] if options.THUMBNAILS else []
        )
        _depth_images: List[Optional[HeifDepthImage]] = (
            [HeifDepthImage(i) for i in c_image.depth_image_list if i is not None] if options.DEPTH_IMAGES else []
        )
        self.info = {
            "primary": bool(c_image.primary),
            "bit_depth": int(c_image.bit_depth),
            "exif": _exif,
            "xmp": _xmp,
            "metadata": _metadata,
            "thumbnails": _thumbnails,
            "depth_images": _depth_images,
        }
        save_colorspace_chroma(c_image, self.info)
        _color_profile: Dict[str, Any] = c_image.color_profile
        if _color_profile:
            if _color_profile["type"] in ("rICC", "prof"):
                self.info["icc_profile"] = _color_profile["data"]
                self.info["icc_profile_type"] = _color_profile["type"]
            else:
                self.info["nclx_profile"] = _color_profile["data"]

    def __repr__(self):
        _bytes = f"{len(self.data)} bytes" if self._data or isinstance(self._c_image, MimCImage) else "no"
        return (
            f"<{self.__class__.__name__} {self.size[0]}x{self.size[1]} {self.mode} "
            f"with {_bytes} image data and {len(self.info.get('thumbnails', []))} thumbnails>"
        )

    @property
    def has_alpha(self) -> bool:
        """``True`` for images with the ``alpha`` channel, ``False`` otherwise."""
        return self.mode.split(sep=";")[0][-1] in ("A", "a")

    @property
    def premultiplied_alpha(self) -> bool:
        """``True`` for images with ``premultiplied alpha`` channel, ``False`` otherwise."""
        return bool(self.mode.split(sep=";")[0][-1] == "a")

    @premultiplied_alpha.setter
    def premultiplied_alpha(self, value: bool):
        if self.has_alpha:
            self.mode = self.mode.replace("A" if value else "a", "a" if value else "A")

    def to_pillow(self) -> Image.Image:
        """Helper method to create :external:py:class:`~PIL.Image.Image` class.

        :returns: :external:py:class:`~PIL.Image.Image` class created from an image.
        """
        image = super().to_pillow()
        image.info = self.info.copy()
        image.info["original_orientation"] = set_orientation(image.info)
        return image


class HeifFile:
    """Representation of the :py:class:`~pillow_heif.HeifImage` classes container.

    To create :py:class:`~pillow_heif.HeifFile` object, use the appropriate factory functions.

    * :py:func:`~pillow_heif.open_heif`
    * :py:func:`~pillow_heif.read_heif`
    * :py:func:`~pillow_heif.from_pillow`
    * :py:func:`~pillow_heif.from_bytes`

    Exceptions that can be raised when working with methods:
        `ValueError`, `EOFError`, `SyntaxError`, `RuntimeError`, `OSError`
    """

    def __init__(self, fp=None, convert_hdr_to_8bit=True, bgr_mode=False, **kwargs):
        if hasattr(fp, "seek"):
            fp.seek(0, SEEK_SET)

        if fp is None:
            images = []
            mimetype = ""
        else:
            fp_bytes = _get_bytes(fp)
            mimetype = get_file_mimetype(fp_bytes)
            if mimetype.find("avif") != -1:
                preferred_decoder = options.PREFERRED_DECODER.get("AVIF", "")
            elif mimetype.find("heic") != -1 or mimetype.find("heif") != -1:
                preferred_decoder = options.PREFERRED_DECODER.get("HEIF", "")
            else:
                preferred_decoder = ""
            images = _pillow_heif.load_file(
                fp_bytes,
                options.DECODE_THREADS,
                convert_hdr_to_8bit,
                bgr_mode,
                kwargs.get("remove_stride", True),
                kwargs.get("hdr_to_16bit", True),
                kwargs.get("reload_size", options.ALLOW_INCORRECT_HEADERS),
                preferred_decoder,
            )
        self.mimetype = mimetype
        self._images: List[HeifImage] = [HeifImage(i) for i in images if i is not None]
        self.primary_index = 0
        for index, _ in enumerate(self._images):
            if _.info.get("primary", False):
                self.primary_index = index

    @property
    def size(self):
        """:attr:`~pillow_heif.HeifImage.size` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].size

    @property
    def mode(self):
        """:attr:`~pillow_heif.HeifImage.mode` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].mode

    @property
    def has_alpha(self):
        """:attr:`~pillow_heif.HeifImage.has_alpha` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].has_alpha

    @property
    def premultiplied_alpha(self):
        """:attr:`~pillow_heif.HeifImage.premultiplied_alpha` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].premultiplied_alpha

    @premultiplied_alpha.setter
    def premultiplied_alpha(self, value: bool):
        self._images[self.primary_index].premultiplied_alpha = value

    @property
    def data(self):
        """:attr:`~pillow_heif.HeifImage.data` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].data

    @property
    def stride(self):
        """:attr:`~pillow_heif.HeifImage.stride` property of the primary :class:`~pillow_heif.HeifImage`.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].stride

    @property
    def info(self):
        """`info`` dict of the primary :class:`~pillow_heif.HeifImage` in the container.

        :exception IndexError: If there are no images.
        """
        return self._images[self.primary_index].info

    def to_pillow(self) -> Image.Image:
        """Helper method to create Pillow :external:py:class:`~PIL.Image.Image`.

        :returns: :external:py:class:`~PIL.Image.Image` class created from the primary image.
        """
        return self._images[self.primary_index].to_pillow()

    def save(self, fp, **kwargs) -> None:
        """Saves image(s) under the given fp.

        Keyword options can be used to provide additional instructions to the writer.
        If a writer does not recognize an option, it is silently ignored.

        Supported options:
            ``save_all`` - boolean. Should all images from ``HeiFile`` be saved?
            (default = ``True``)

            ``append_images`` - do the same as in Pillow. Accepts the list of ``HeifImage``

            .. note:: Appended images always will have ``info["primary"]=False``

            ``quality`` - see :py:attr:`~pillow_heif.options.QUALITY`

            ``enc_params`` - dictionary with key:value to pass to :ref:`x265 <hevc-encoder>` encoder.

            ``exif`` - override primary image's EXIF with specified.
            Accepts ``None``, ``bytes`` or ``PIL.Image.Exif`` class.

            ``xmp`` - override primary image's XMP with specified. Accepts ``None`` or ``bytes``.

            ``primary_index`` - ignore ``info["primary"]`` and set `PrimaryImage` by index.

            ``chroma`` - custom subsampling value. Possible values: ``444``, ``422`` or ``420`` (``x265`` default).

            ``subsampling`` - synonym for *chroma*. Format is string, compatible with Pillow: ``x:x:x``, e.g. '4:4:4'.

            ``format`` - string with encoder format name. Possible values: ``HEIF`` (default) or ``AVIF``.

            ``save_nclx_profile`` - boolean, see :py:attr:`~pillow_heif.options.SAVE_NCLX_PROFILE`

            ``matrix_coefficients`` - int, nclx profile: color conversion matrix coefficients, default=6 (see h.273)

            ``color_primaries`` - int, nclx profile: color primaries (see h.273)

            ``transfer_characteristic`` - int, nclx profile: transfer characteristics (see h.273)

            ``full_range_flag`` - nclx profile: full range flag, default: 1

        :param fp: A filename (string), pathlib.Path object or an object with `write` method.
        """
        _encode_images(self._images, fp, **kwargs)

    def __repr__(self):
        return f"<{self.__class__.__name__} with {len(self)} images: {[str(i) for i in self]}>"

    def __len__(self):
        return len(self._images)

    def __iter__(self):
        yield from self._images

    def __getitem__(self, index):
        if index < 0 or index >= len(self._images):
            raise IndexError(f"invalid image index: {index}")
        return self._images[index]

    def __delitem__(self, key):
        if key < 0 or key >= len(self._images):
            raise IndexError(f"invalid image index: {key}")
        del self._images[key]

    def add_frombytes(self, mode: str, size: tuple, data, **kwargs):
        """Adds image from bytes to container.

        .. note:: Supports ``stride`` value if needed.

        :param mode: see :ref:`image-modes`.
        :param size: tuple with ``width`` and ``height`` of image.
        :param data: bytes object with raw image data.

        :returns: :py:class:`~pillow_heif.HeifImage` added object.
        """
        added_image = HeifImage(MimCImage(mode, size, data, **kwargs))
        self._images.append(added_image)
        return added_image

    def add_from_heif(self, image: HeifImage) -> HeifImage:
        """Add image to the container.

        :param image: :py:class:`~pillow_heif.HeifImage` class to add from.

        :returns: :py:class:`~pillow_heif.HeifImage` added object.
        """
        image.load()
        added_image = self.add_frombytes(
            image.mode,
            image.size,
            image.data,
            stride=image.stride,
        )
        added_image.info = deepcopy(image.info)
        added_image.info.pop("primary", None)
        return added_image

    def add_from_pillow(self, image: Image.Image) -> HeifImage:
        """Add image to the container.

        :param image: Pillow :external:py:class:`~PIL.Image.Image` class to add from.

        :returns: :py:class:`~pillow_heif.HeifImage` added object.
        """
        if image.size[0] <= 0 or image.size[1] <= 0:
            raise ValueError("Empty images are not supported.")
        _info = image.info.copy()
        _info["exif"] = _exif_from_pillow(image)
        _info["xmp"] = _xmp_from_pillow(image)
        original_orientation = set_orientation(_info)
        _img = _pil_to_supported_mode(image)
        if original_orientation is not None and original_orientation != 1:
            _img = _rotate_pil(_img, original_orientation)
        _img.load()
        added_image = self.add_frombytes(
            _img.mode,
            _img.size,
            _img.tobytes(),
        )
        for key in ["bit_depth", "thumbnails", "icc_profile", "icc_profile_type"]:
            if key in image.info:
                added_image.info[key] = image.info[key]
        for key in ["nclx_profile", "metadata"]:
            if key in image.info:
                added_image.info[key] = deepcopy(image.info[key])
        added_image.info["exif"] = _exif_from_pillow(image)
        added_image.info["xmp"] = _xmp_from_pillow(image)
        return added_image

    @property
    def __array_interface__(self):
        """Returns the primary image as a numpy array."""
        return self._images[self.primary_index].__array_interface__

    def __getstate__(self):
        im_desc = []
        for im in self._images:
            im_data = bytes(im.data)
            im_desc.append([im.mode, im.size, im_data, im.info])
        return [self.primary_index, self.mimetype, im_desc]

    def __setstate__(self, state):
        self.__init__()
        self.primary_index, self.mimetype, images = state
        for im_desc in images:
            im_mode, im_size, im_data, im_info = im_desc
            added_image = self.add_frombytes(im_mode, im_size, im_data)
            added_image.info = im_info

    def __copy(self):
        _im_copy = HeifFile()
        _im_copy._images = copy(self._images)  # pylint: disable=protected-access
        _im_copy.mimetype = self.mimetype
        _im_copy.primary_index = self.primary_index
        return _im_copy

    __copy__ = __copy


def is_supported(fp) -> bool:
    """Checks if the given `fp` object contains a supported file type.

    :param fp: A filename (string), pathlib.Path object or a file object.
        The file object must implement ``file.read``, ``file.seek``, and ``file.tell`` methods,
        and be opened in binary mode.

    :returns: A boolean indicating if the object can be opened.
    """
    __data = _get_bytes(fp, 12)
    if __data[4:8] != b"ftyp":
        return False
    return get_file_mimetype(__data) != ""


def open_heif(fp, convert_hdr_to_8bit=True, bgr_mode=False, **kwargs) -> HeifFile:
    """Opens the given HEIF(AVIF) image file.

    :param fp: See parameter ``fp`` in :func:`is_supported`
    :param convert_hdr_to_8bit: Boolean indicating should 10 bit or 12 bit images
        be converted to 8-bit images during decoding. Otherwise, they will open in 16-bit mode.
        ``Does not affect "monochrome" or "depth images".``
    :param bgr_mode: Boolean indicating should be `RGB(A)` images be opened in `BGR(A)` mode.
    :param kwargs: **hdr_to_16bit** a boolean value indicating that 10/12-bit image data
        should be converted to 16-bit mode during decoding. `Has lower priority than convert_hdr_to_8bit`!
        Default = **True**

    :returns: :py:class:`~pillow_heif.HeifFile` object.
    :exception ValueError: invalid input data.
    :exception EOFError: corrupted image data.
    :exception SyntaxError: unsupported feature.
    :exception RuntimeError: some other error.
    :exception OSError: out of memory.
    """
    return HeifFile(fp, convert_hdr_to_8bit, bgr_mode, **kwargs)


def read_heif(fp, convert_hdr_to_8bit=True, bgr_mode=False, **kwargs) -> HeifFile:
    """Opens the given HEIF(AVIF) image file and decodes all images.

    .. note:: In most cases it is better to call :py:meth:`~pillow_heif.open_heif`, and
        let images decoded automatically only when needed.

    :param fp: See parameter ``fp`` in :func:`is_supported`
    :param convert_hdr_to_8bit: Boolean indicating should 10 bit or 12 bit images
        be converted to 8-bit images during decoding. Otherwise, they will open in 16-bit mode.
        ``Does not affect "monochrome" or "depth images".``
    :param bgr_mode: Boolean indicating should be `RGB(A)` images be opened in `BGR(A)` mode.
    :param kwargs: **hdr_to_16bit** a boolean value indicating that 10/12-bit image data
        should be converted to 16-bit mode during decoding. `Has lower priority than convert_hdr_to_8bit`!
        Default = **True**

    :returns: :py:class:`~pillow_heif.HeifFile` object.
    :exception ValueError: invalid input data.
    :exception EOFError: corrupted image data.
    :exception SyntaxError: unsupported feature.
    :exception RuntimeError: some other error.
    :exception OSError: out of memory.
    """
    ret = HeifFile(fp, convert_hdr_to_8bit, bgr_mode, reload_size=True, **kwargs)
    for img in ret:
        img.load()
    return ret


def encode(mode: str, size: tuple, data, fp, **kwargs) -> None:
    """Encodes data in a ``fp``.

    :param mode: `BGR(A);16`, `RGB(A);16`, LA;16`, `L;16`, `I;16L`, `BGR(A)`, `RGB(A)`, `LA`, `L`
    :param size: tuple with ``width`` and ``height`` of an image.
    :param data: bytes object with raw image data.
    :param fp: A filename (string), pathlib.Path object or an object with ``write`` method.
    """
    _encode_images([HeifImage(MimCImage(mode, size, data, **kwargs))], fp, **kwargs)


def _encode_images(images: List[HeifImage], fp, **kwargs) -> None:
    compression = kwargs.get("format", "HEIF")
    compression_format = HeifCompressionFormat.AV1 if compression == "AVIF" else HeifCompressionFormat.HEVC
    if not _pillow_heif.get_lib_info()[compression]:
        raise RuntimeError(f"No {compression} encoder found.")
    images_to_save: List[HeifImage] = images + kwargs.get("append_images", [])
    if not kwargs.get("save_all", True):
        images_to_save = images_to_save[:1]
    if not images_to_save:
        raise ValueError("Cannot write file with no images as HEIF.")
    primary_index = _get_primary_index(images_to_save, kwargs.get("primary_index", None))
    ctx_write = CtxEncode(compression_format, **kwargs)
    for i, img in enumerate(images_to_save):
        img.load()
        _info = img.info.copy()
        _info["primary"] = False
        if i == primary_index:
            _info.update(**kwargs)
            _info["primary"] = True
        _info.pop("stride", 0)
        ctx_write.add_image(
            img.size,
            img.mode,
            img.data,
            image_orientation=_get_orientation_for_encoder(_info),
            **_info,
            stride=img.stride,
        )
    ctx_write.save(fp)


def from_pillow(pil_image: Image.Image) -> HeifFile:
    """Creates :py:class:`~pillow_heif.HeifFile` from a Pillow Image.

    :param pil_image: Pillow :external:py:class:`~PIL.Image.Image` class.

    :returns: New :py:class:`~pillow_heif.HeifFile` object.
    """
    _ = HeifFile()
    _.add_from_pillow(pil_image)
    return _


def from_bytes(mode: str, size: tuple, data, **kwargs) -> HeifFile:
    """Creates :py:class:`~pillow_heif.HeifFile` from bytes.

    .. note:: Supports ``stride`` value if needed.

    :param mode: see :ref:`image-modes`.
    :param size: tuple with ``width`` and ``height`` of an image.
    :param data: bytes object with raw image data.

    :returns: New :py:class:`~pillow_heif.HeifFile` object.
    """
    _ = HeifFile()
    _.add_frombytes(mode, size, data, **kwargs)
    return _
