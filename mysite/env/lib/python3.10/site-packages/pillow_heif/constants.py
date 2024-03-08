"""Enums from LibHeif that are used."""

from enum import IntEnum


class HeifChroma(IntEnum):
    """Chroma subsampling definitions."""

    UNDEFINED = 99
    """Undefined chroma."""
    MONOCHROME = 0
    """Mono chroma."""
    CHROMA_420 = 1
    """``Cb`` and ``Cr`` are each subsampled at a factor of 2 both horizontally and vertically."""
    CHROMA_422 = 2
    """The two chroma components are sampled at half the horizontal sample rate of luma."""
    CHROMA_444 = 3
    """Each of the three Y'CbCr components has the same sample rate."""
    INTERLEAVED_RGB = 10
    """Simple interleaved RGB."""
    INTERLEAVED_RGBA = 11
    """Interleaved RGB with Alpha channel."""
    INTERLEAVED_RRGGBB_BE = 12
    """10 bit RGB BE."""
    INTERLEAVED_RRGGBBAA_BE = 13
    """10 bit RGB BE with Alpha channel."""
    INTERLEAVED_RRGGBB_LE = 14
    """10 bit RGB LE."""
    INTERLEAVED_RRGGBBAA_LE = 15
    """10 bit RGB LE with Alpha channel."""


class HeifColorspace(IntEnum):
    """Colorspace format of the image."""

    UNDEFINED = 99
    """Undefined colorspace."""
    YCBCR = 0
    """https://en.wikipedia.org/wiki/YCbCr"""
    RGB = 1
    """RGB colorspace."""
    MONOCHROME = 2
    """Monochrome colorspace."""


class HeifCompressionFormat(IntEnum):
    """Possible LibHeif compression formats."""

    UNDEFINED = 0
    """The compression format is not defined."""
    HEVC = 1
    """Equivalent to H.265."""
    AVC = 2
    """Equivalent to H.264. Defined in ISO/IEC 14496-10."""
    JPEG = 3
    """JPEG compression. Defined in ISO/IEC 10918-1."""
    AV1 = 4
    """AV1 compression, used for AVIF images."""
    VVC = 5
    """Equivalent to H.266. Defined in ISO/IEC 23090-3."""
    EVC = 6
    """Equivalent to H.266. Defined in ISO/IEC 23094-1."""
    JPEG2000 = 7
    """The compression format is JPEG200 ISO/IEC 15444-16:2021"""
    UNCOMPRESSED = 8
    """Defined in ISO/IEC 23001-17:2023 (Final Draft International Standard)."""
    MASK = 9
    """Mask image encoding. See ISO/IEC 23008-12:2022 Section 6.10.2"""


class HeifColorPrimaries(IntEnum):
    """Possible NCLX color_primaries values."""

    ITU_R_BT_709_5 = 1
    """g=0.3;0.6, b=0.15;0.06, r=0.64;0.33, w=0.3127,0.3290"""
    UNSPECIFIED = 2
    """No color primaries"""
    ITU_R_BT_470_6_SYSTEM_M = 4
    """Unknown"""
    ITU_R_BT_470_6_SYSTEM_B_G = 5
    """Unknown"""
    ITU_R_BT_601_6 = 6
    """Unknown"""
    SMPTE_240M = 7
    """Unknown"""
    GENERIC_FILM = 8
    """Unknown"""
    ITU_R_BT_2020_2_AND_2100_0 = 9
    """Unknown"""
    SMPTE_ST_428_1 = 10
    """Unknown"""
    SMPTE_RP_431_2 = 11
    """Unknown"""
    SMPTE_EG_432_1 = 12
    """Unknown"""
    EBU_TECH_3213_E = 22
    """Unknown"""


class HeifTransferCharacteristics(IntEnum):
    """Possible NCLX transfer_characteristics values."""

    ITU_R_BT_709_5 = 1
    """Unknown"""
    UNSPECIFIED = 2
    """No transfer characteristics"""
    ITU_R_BT_470_6_SYSTEM_M = 4
    """Unknown"""
    ITU_R_BT_470_6_SYSTEM_B_G = 5
    """Unknown"""
    ITU_R_BT_601_6 = 6
    """Unknown"""
    SMPTE_240M = 7
    """Unknown"""
    LINEAR = 8
    """Unknown"""
    LOGARITHMIC_100 = 9
    """Unknown"""
    LOGARITHMIC_100_SQRT10 = 10
    """Unknown"""
    IEC_61966_2_4 = 11
    """Unknown"""
    ITU_R_BT_1361 = 12
    """Unknown"""
    IEC_61966_2_1 = 13
    """Unknown"""
    ITU_R_BT_2020_2_10BIT = 14
    """Unknown"""
    ITU_R_BT_2020_2_12BIT = 15
    """Unknown"""
    ITU_R_BT_2100_0_PQ = 16
    """Unknown"""
    SMPTE_ST_428_1 = 17
    """Unknown"""
    ITU_R_BT_2100_0_HLG = 18
    """Unknown"""


class HeifMatrixCoefficients(IntEnum):
    """Possible NCLX matrix_coefficients values."""

    RGB_GBR = 0
    """Unknown"""
    ITU_R_BT_709_5 = 1
    """Unknown"""
    UNSPECIFIED = 2
    """Unknown"""
    US_FCC_T47 = 4
    """Unknown"""
    ITU_R_BT_470_6_SYSTEM_B_G = 5
    """Unknown"""
    ITU_R_BT_601_6 = 6
    """Unknown"""
    SMPTE_240M = 7
    """Unknown"""
    YCGCO = 8
    """Unknown"""
    ITU_R_BT_2020_2_NON_CONSTANT_LUMINANCE = 9
    """Unknown"""
    ITU_R_BT_2020_2_CONSTANT_LUMINANCE = 10
    """Unknown"""
    SMPTE_ST_2085 = 11
    """Unknown"""
    CHROMATICITY_DERIVED_NON_CONSTANT_LUMINANCE = 12
    """Unknown"""
    CHROMATICITY_DERIVED_CONSTANT_LUMINANCE = 13
    """Unknown"""
    ICTCP = 14
    """Unknown"""


class HeifDepthRepresentationType(IntEnum):
    """Possible values of the ``HeifDepthImage.info['metadata']['representation_type']``."""

    UNIFORM_INVERSE_Z = 0
    """Unknown"""
    UNIFORM_DISPARITY = 1
    """Unknown"""
    UNIFORM_Z = 2
    """Unknown"""
    NON_UNIFORM_DISPARITY = 3
    """Unknown"""


class HeifChannel(IntEnum):
    """Internal libheif values, used in ``CtxEncode``."""

    CHANNEL_Y = 0
    """Monochrome or YCbCR"""
    CHANNEL_CB = 1
    """Only for YCbCR"""
    CHANNEL_CR = 2
    """Only for YCbCR"""
    CHANNEL_R = 3
    """RGB or RGBA"""
    CHANNEL_G = 4
    """RGB or RGBA"""
    CHANNEL_B = 5
    """RGB or RGBA"""
    CHANNEL_ALPHA = 6
    """Monochrome or RGBA"""
    CHANNEL_INTERLEAVED = 10
    """RGB or RGBA"""
