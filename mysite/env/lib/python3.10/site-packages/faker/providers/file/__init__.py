import string

from collections import OrderedDict
from typing import Dict, Literal, Optional, Sequence, Union

from .. import BaseProvider, ElementsType


class Provider(BaseProvider):
    """Implement default file provider for Faker."""

    application_mime_types: ElementsType[str] = (
        "application/atom+xml",  # Atom feeds
        "application/ecmascript",
        # ECMAScript/JavaScript; Defined in RFC 4329 (equivalent to
        # application/javascript but with stricter processing rules)
        "application/EDI-X12",  # EDI X12 data; Defined in RFC 1767
        "application/EDIFACT",  # EDI EDIFACT data; Defined in RFC 1767
        "application/json",  # JavaScript Object Notation JSON; Defined in RFC 4627
        # ECMAScript/JavaScript; Defined in RFC 4329 (equivalent to
        # application/ecmascript
        "application/javascript",
        #   but with looser processing rules) It is not accepted in IE 8
        #   or earlier - text/javascript is accepted but it is defined as obsolete in RFC 4329.
        #   The "type" attribute of the <script> tag in HTML5 is optional and in practice
        #   omitting the media type of JavaScript programs is the most interoperable
        #   solution since all browsers have always assumed the correct
        #   default even before HTML5.
        "application/octet-stream",
        # Arbitrary binary data.[6] Generally speaking this type identifies files that are not associated with
        # a specific application. Contrary to past assumptions by software packages such as Apache this is not
        # a type that should be applied to unknown files. In such a case, a server or application should not indicate
        # a content type, as it may be incorrect, but rather, should omit the type in order to allow the recipient
        # to guess the type.[7]
        "application/ogg",  # Ogg, a multimedia bitstream container format; Defined in RFC 5334
        "application/pdf",  # Portable Document Format, PDF has been in use for document exchange
        #   on the Internet since 1993; Defined in RFC 3778
        "application/postscript",  # PostScript; Defined in RFC 2046
        "application/rdf+xml",  # Resource Description Framework; Defined by RFC 3870
        "application/rss+xml",  # RSS feeds
        "application/soap+xml",  # SOAP; Defined by RFC 3902
        # Web Open Font Format; (candidate recommendation; use application/x-font-woff
        "application/font-woff",
        #   until standard is official)
        "application/xhtml+xml",  # XHTML; Defined by RFC 3236
        "application/xml-dtd",  # DTD files; Defined by RFC 3023
        "application/xop+xml",  # XOP
        "application/zip",  # ZIP archive files; Registered[8]
        "application/gzip",  # Gzip, Defined in RFC 6713
    )

    audio_mime_types: ElementsType[str] = (
        "audio/basic",  # mulaw audio at 8 kHz, 1 channel; Defined in RFC 2046
        "audio/L24",  # 24bit Linear PCM audio at 8-48 kHz, 1-N channels; Defined in RFC 3190
        "audio/mp4",  # MP4 audio
        "audio/mpeg",  # MP3 or other MPEG audio; Defined in RFC 3003
        "audio/ogg",  # Ogg Vorbis, Speex, Flac and other audio; Defined in RFC 5334
        "audio/vorbis",  # Vorbis encoded audio; Defined in RFC 5215
        # RealAudio; Documented in RealPlayer Help[9]
        "audio/vnd.rn-realaudio",
        "audio/vnd.wave",  # WAV audio; Defined in RFC 2361
        "audio/webm",  # WebM open media format
    )

    image_mime_types: ElementsType[str] = (
        "image/gif",  # GIF image; Defined in RFC 2045 and RFC 2046
        "image/jpeg",  # JPEG JFIF image; Defined in RFC 2045 and RFC 2046
        "image/pjpeg",
        # JPEG JFIF image; Associated with Internet Explorer; Listed in ms775147(v=vs.85) - Progressive JPEG,
        # initiated before global browser support for progressive JPEGs (Microsoft and Firefox).
        # Portable Network Graphics; Registered,[10] Defined in RFC 2083
        "image/png",
        "image/svg+xml",  # SVG vector image; Defined in SVG Tiny 1.2 Specification Appendix M
        # Tag Image File Format (only for Baseline TIFF); Defined in RFC 3302
        "image/tiff",
        "image/vnd.microsoft.icon",  # ICO image; Registered[11]
    )

    message_mime_types: ElementsType[str] = (
        "message/http",  # Defined in RFC 2616
        "message/imdn+xml",  # IMDN Instant Message Disposition Notification; Defined in RFC 5438
        "message/partial",  # Email; Defined in RFC 2045 and RFC 2046
        # Email; EML files, MIME files, MHT files, MHTML files; Defined in RFC
        # 2045 and RFC 2046
        "message/rfc822",
    )

    model_mime_types: ElementsType[str] = (
        "model/example",  # Defined in RFC 4735
        "model/iges",  # IGS files, IGES files; Defined in RFC 2077
        "model/mesh",  # MSH files, MESH files; Defined in RFC 2077, SILO files
        "model/vrml",  # WRL files, VRML files; Defined in RFC 2077
        # X3D ISO standard for representing 3D computer graphics, X3DB binary
        # files
        "model/x3d+binary",
        "model/x3d+vrml",  # X3D ISO standard for representing 3D computer graphics, X3DV VRML files
        "model/x3d+xml",  # X3D ISO standard for representing 3D computer graphics, X3D XML files
    )

    multipart_mime_types: ElementsType[str] = (
        "multipart/mixed",  # MIME Email; Defined in RFC 2045 and RFC 2046
        "multipart/alternative",  # MIME Email; Defined in RFC 2045 and RFC 2046
        # MIME Email; Defined in RFC 2387 and used by MHTML (HTML mail)
        "multipart/related",
        "multipart/form-data",  # MIME Webform; Defined in RFC 2388
        "multipart/signed",  # Defined in RFC 1847
        "multipart/encrypted",  # Defined in RFC 1847
    )

    text_mime_types: ElementsType[str] = (
        "text/cmd",  # commands; subtype resident in Gecko browsers like Firefox 3.5
        "text/css",  # Cascading Style Sheets; Defined in RFC 2318
        "text/csv",  # Comma-separated values; Defined in RFC 4180
        "text/html",  # HTML; Defined in RFC 2854
        "text/javascript",
        # (Obsolete): JavaScript; Defined in and obsoleted by RFC 4329 in order to discourage its usage in favor of
        # application/javascript. However, text/javascript is allowed in HTML 4 and 5 and, unlike
        # application/javascript, has cross-browser support. The "type" attribute of the <script> tag in HTML5 is
        # optional and there is no need to use it at all since all browsers have always assumed the correct default
        # (even in HTML 4 where it was required by the specification).
        "text/plain",  # Textual data; Defined in RFC 2046 and RFC 3676
        "text/vcard",  # vCard (contact information); Defined in RFC 6350
        "text/xml",  # Extensible Markup Language; Defined in RFC 3023
    )

    video_mime_types: ElementsType[str] = (
        "video/mpeg",  # MPEG-1 video with multiplexed audio; Defined in RFC 2045 and RFC 2046
        "video/mp4",  # MP4 video; Defined in RFC 4337
        # Ogg Theora or other video (with audio); Defined in RFC 5334
        "video/ogg",
        "video/quicktime",  # QuickTime video; Registered[12]
        "video/webm",  # WebM Matroska-based open media format
        "video/x-matroska",  # Matroska open media format
        "video/x-ms-wmv",  # Windows Media Video; Documented in Microsoft KB 288102
        "video/x-flv",  # Flash video (FLV files)
    )

    mime_types: Dict[str, ElementsType[str]] = OrderedDict(
        (
            ("application", application_mime_types),
            ("audio", audio_mime_types),
            ("image", image_mime_types),
            ("message", message_mime_types),
            ("model", model_mime_types),
            ("multipart", multipart_mime_types),
            ("text", text_mime_types),
            ("video", video_mime_types),
        )
    )

    audio_file_extensions: ElementsType[str] = (
        "flac",
        "mp3",
        "wav",
    )

    image_file_extensions: ElementsType[str] = (
        "bmp",
        "gif",
        "jpeg",
        "jpg",
        "png",
        "tiff",
    )

    text_file_extensions: ElementsType[str] = (
        "css",
        "csv",
        "html",
        "js",
        "json",
        "txt",
    )

    video_file_extensions: ElementsType[str] = (
        "mp4",
        "avi",
        "mov",
        "webm",
    )

    office_file_extensions: ElementsType[str] = (
        "doc",  # legacy MS Word
        "docx",  # MS Word
        "xls",  # legacy MS Excel
        "xlsx",  # MS Excel
        "ppt",  # legacy MS PowerPoint
        "pptx",  # MS PowerPoint
        "odt",  # LibreOffice document
        "ods",  # LibreOffice spreadsheet
        "odp",  # LibreOffice presentation
        "pages",  # Apple Pages
        "numbers",  # Apple Numbers
        "key",  # Apple Keynote
        "pdf",  # Portable Document Format
    )

    file_extensions: Dict[str, ElementsType[str]] = OrderedDict(
        (
            ("audio", audio_file_extensions),
            ("image", image_file_extensions),
            ("office", office_file_extensions),
            ("text", text_file_extensions),
            ("video", video_file_extensions),
        )
    )

    file_systems_path_rules: Dict[str, Dict] = {
        "windows": {
            "root": "C:\\",
            "separator": "\\",
        },
        "linux": {
            "root": "/",
            "separator": "/",
        },
    }

    unix_device_prefixes: ElementsType[str] = ("sd", "vd", "xvd")

    def mime_type(self, category: Optional[str] = None) -> str:
        """Generate a mime type under the specified ``category``.

        If ``category`` is ``None``, a random category will be used. The list of
        valid categories include ``'application'``, ``'audio'``, ``'image'``,
        ``'message'``, ``'model'``, ``'multipart'``, ``'text'``, and
        ``'video'``.

        :sample:
        :sample: category='application'
        """
        category = category if category else self.random_element(list(self.mime_types.keys()))
        return self.random_element(self.mime_types[category])

    def file_name(self, category: Optional[str] = None, extension: Optional[str] = None) -> str:
        """Generate a random file name with extension.

        If ``extension`` is ``None``, a random extension will be created
        under the hood using |file_extension| with the specified
        ``category``. If a value for ``extension`` is provided, the
        value will be used instead, and ``category`` will be ignored.
        The actual name part itself is generated using |word|. If
        extension is an empty string then no extension will be added,
        and file_name will be the same as |word|.

        :sample: size=10
        :sample: category='audio'
        :sample: extension='abcdef'
        :sample: category='audio', extension='abcdef'
        :sample: extension=''
        """
        if extension is None:
            extension = self.file_extension(category)
        filename: str = self.generator.word()
        return f"{filename}.{extension}" if extension else filename

    def file_extension(self, category: Optional[str] = None) -> str:
        """Generate a file extension under the specified ``category``.

        If ``category`` is ``None``, a random category will be used. The list of
        valid categories include: ``'audio'``, ``'image'``, ``'office'``,
        ``'text'``, and ``'video'``.

        :sample:
        :sample: category='image'
        """
        if category is None:
            category = self.random_element(list(self.file_extensions.keys()))
        return self.random_element(self.file_extensions[category])

    def file_path(
        self,
        depth: int = 1,
        category: Optional[str] = None,
        extension: Optional[Union[str, Sequence[str]]] = None,
        absolute: Optional[bool] = True,
        file_system_rule: Literal["linux", "windows"] = "linux",
    ) -> str:
        """Generate an pathname to a file.

        This method uses |file_name| under the hood to generate the file
        name itself, and ``depth`` controls the depth of the directory
        path, and |word| is used under the hood to generate the
        different directory names.

        If ``absolute`` is ``True`` (default), the generated path starts
        with ``/`` and is absolute. Otherwise, the generated path is
        relative.

        If used, ``extension`` can be either a string, forcing that
        extension, a sequence of strings (one will be picked at random),
        or an empty sequence (the path will have no extension). Default
        behaviour is the same as |file_name|

        if ``file_system`` is set (default="linux"), the generated path uses
        specified file system path standard, the list of valid file systems include:
        ``'windows'``, ``'linux'``.

        :sample: size=10
        :sample: depth=3
        :sample: depth=5, category='video'
        :sample: depth=5, category='video', extension='abcdef'
        :sample: extension=[]
        :sample: extension=''
        :sample: extension=["a", "bc", "def"]
        :sample: depth=5, category='video', extension='abcdef', file_system='windows'
        """

        if extension is not None and not isinstance(extension, str):
            if len(extension):
                extension = self.random_element(extension)
            else:
                extension = ""

        fs_rule = self.file_systems_path_rules.get(file_system_rule, None)
        if not fs_rule:
            raise TypeError("Specified file system is invalid.")

        root = fs_rule["root"]
        seperator = fs_rule["separator"]

        path: str = self.file_name(category, extension)
        for _ in range(0, depth):
            path = f"{self.generator.word()}{seperator}{path}"

        return root + path if absolute else path

    def unix_device(self, prefix: Optional[str] = None) -> str:
        """Generate a Unix device file name.

        If ``prefix`` is ``None``, a random prefix will be used. The list of
        valid prefixes include: ``'sd'``, ``'vd'``, and ``'xvd'``.

        :sample:
        :sample: prefix='mmcblk'
        """
        if prefix is None:
            prefix = self.random_element(self.unix_device_prefixes)
        suffix: str = self.random_element(string.ascii_lowercase)
        path = "/dev/%s%s" % (prefix, suffix)
        return path

    def unix_partition(self, prefix: Optional[str] = None) -> str:
        """Generate a Unix partition name.

        This method uses |unix_device| under the hood to create a device file
        name with the specified ``prefix``.

        :sample:
        :sample: prefix='mmcblk'
        """
        path: str = self.unix_device(prefix=prefix)
        path += str(self.random_digit())
        return path
