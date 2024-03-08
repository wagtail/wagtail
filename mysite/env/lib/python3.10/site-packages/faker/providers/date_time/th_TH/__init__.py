import warnings

from datetime import datetime
from typing import Optional

from ....typing import DateParseType
from .. import Provider as DateParseTypeProvider

# thai_strftime() code adapted from
# https://gist.github.com/bact/b8afe49cb1ae62913e6c1e899dcddbdb
# (Same code base with PyThaiNLP 2.x)
# Public Domain or CC0 1.0 Universal

_TH_ABBR_WEEKDAYS = ["จ", "อ", "พ", "พฤ", "ศ", "ส", "อา"]
_TH_FULL_WEEKDAYS = [
    "วันจันทร์",
    "วันอังคาร",
    "วันพุธ",
    "วันพฤหัสบดี",
    "วันศุกร์",
    "วันเสาร์",
    "วันอาทิตย์",
]

_TH_ABBR_MONTHS = [
    "ม.ค.",
    "ก.พ.",
    "มี.ค.",
    "เม.ย.",
    "พ.ค.",
    "มิ.ย.",
    "ก.ค.",
    "ส.ค.",
    "ก.ย.",
    "ต.ค.",
    "พ.ย.",
    "ธ.ค.",
]
_TH_FULL_MONTHS = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]

_HA_TH_DIGITS = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
_BE_AD_DIFFERENCE = 543

_NEED_L10N = "AaBbCcDFGgvXxYy+"  # flags that need localization
_EXTENSIONS = "EO-_0^#"  # extension flags


# Standard conversion support for thai_strftime()
def _std_strftime(dt_obj: datetime, fmt_char: str) -> str:
    """
    Standard datetime.strftime() with normalization and exception handling.
    """
    str_ = ""
    try:
        str_ = dt_obj.strftime(f"%{fmt_char}")
        if not str_ or str_ == f"%{fmt_char}":
            # normalize outputs for unsupported directives
            # in different platforms
            # "%Q" may result "%Q", "Q", or "", make it "Q"
            str_ = fmt_char
    except ValueError as err:  # pragma: no cover
        # Unsupported directives may raise ValueError on Windows,
        # in that case just use the fmt_char
        warnings.warn(
            (f"String format directive unknown/not support: %{fmt_char}" f"The system raises this ValueError: {err}"),
            UserWarning,
        )
        str_ = fmt_char
    return str_


# Thai conversion support for thai_strftime()
def _thai_strftime(
    dt_obj: datetime,
    fmt_char: str,
    buddhist_era: bool = True,
) -> str:
    """
    Conversion support for thai_strftime().

    The fmt_char should be in _NEED_L10N when call this function.
    """
    str_ = ""
    year = dt_obj.year
    if buddhist_era:
        year = year + _BE_AD_DIFFERENCE

    if fmt_char == "A":
        # National representation of the full weekday name
        str_ = _TH_FULL_WEEKDAYS[dt_obj.weekday()]
    elif fmt_char == "a":
        # National representation of the abbreviated weekday
        str_ = _TH_ABBR_WEEKDAYS[dt_obj.weekday()]
    elif fmt_char == "B":
        # National representation of the full month name
        str_ = _TH_FULL_MONTHS[dt_obj.month - 1]
    elif fmt_char == "b":
        # National representation of the abbreviated month name
        str_ = _TH_ABBR_MONTHS[dt_obj.month - 1]
    elif fmt_char == "C":
        # Thai Buddhist century (AD+543)/100 + 1 as decimal number;
        str_ = str(int(year / 100) + 1).zfill(2)
    elif fmt_char == "c":
        # Locale’s appropriate date and time representation
        # Wed  6 Oct 01:40:00 1976
        # พ   6 ต.ค. 01:40:00 2519  <-- left-aligned weekday, right-aligned day
        str_ = (
            f"{_TH_ABBR_WEEKDAYS[dt_obj.weekday()]:<2} {dt_obj.day:>2} "
            f"{_TH_ABBR_MONTHS[dt_obj.month - 1]} {dt_obj:%H:%M:%S} {year:04}"
        )
    elif fmt_char == "D":
        # Equivalent to ``%m/%d/%y''
        str_ = f"{dt_obj:%m/%d}/{year % 100:02}"
    elif fmt_char == "F":
        # Equivalent to ``%Y-%m-%d''
        str_ = f"{year:04}-{dt_obj:%m-%d}"
    elif fmt_char == "G":
        # ISO 8601 year with century representing the year that contains
        # the greater part of the ISO week (%V). Monday as the first day
        # of the week.
        year_G = int(dt_obj.strftime("%G"))
        if buddhist_era:
            year_G = year_G + _BE_AD_DIFFERENCE
        str_ = f"{year_G:04}"
    elif fmt_char == "g":
        # Same year as in ``%G'',
        # but as a decimal number without century (00-99).
        year_G = int(dt_obj.strftime("%G"))
        if buddhist_era:
            year_G = year_G + _BE_AD_DIFFERENCE
        str_ = f"{year_G % 100:02}"
    elif fmt_char == "v":
        # BSD extension, ' 6-Oct-1976'
        str_ = f"{dt_obj.day:>2}-{_TH_ABBR_MONTHS[dt_obj.month - 1]}-{year:04}"
    elif fmt_char == "X":
        # Locale’s appropriate time representation.
        str_ = f"{dt_obj:%H:%M:%S}"
    elif fmt_char == "x":
        # Locale’s appropriate date representation.
        str_ = f"{dt_obj:%d/%m}/{year:04}"
    elif fmt_char == "Y":
        # Year with century
        str_ = f"{year:04}"
    elif fmt_char == "y":
        # Year without century
        str_ = f"{year % 100:02}"
    elif fmt_char == "+":
        # National representation of the date and time
        # (the format is similar to that produced by date(1))
        # Wed  6 Oct 1976 01:40:00
        str_ = (
            f"{_TH_ABBR_WEEKDAYS[dt_obj.weekday()]:<2} {dt_obj.day:>2} "
            f"{_TH_ABBR_MONTHS[dt_obj.month - 1]} {year} {dt_obj:%H:%M:%S}"
        )

    return str_


def thai_strftime(
    dt_obj: datetime,
    fmt: str = "%-d %b %Y",
    thai_digit: bool = False,
    buddhist_era: bool = True,
) -> str:
    """
    Convert :class:`datetime.datetime` into Thai date and time format.

    The formatting directives are similar to :func:`datatime.strrftime`.

    This function uses Thai names and Thai Buddhist Era for these directives:
        * **%a** - abbreviated weekday name
        (i.e. "จ", "อ", "พ", "พฤ", "ศ", "ส", "อา")
        * **%A** - full weekday name
        (i.e. "วันจันทร์", "วันอังคาร", "วันเสาร์", "วันอาทิตย์")
        * **%b** - abbreviated month name
        (i.e. "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ธ.ค.")
        * **%B** - full month name
        (i.e. "มกราคม", "กุมภาพันธ์", "พฤศจิกายน", "ธันวาคม",)
        * **%y** - year without century (i.e. "56", "10")
        * **%Y** - year with century (i.e. "2556", "2410")
        * **%c** - date and time representation
        (i.e. "พ   6 ต.ค. 01:40:00 2519")
        * **%v** - short date representation
        (i.e. " 6-ม.ค.-2562", "27-ก.พ.-2555")
    """
    thaidate_parts = []

    i = 0
    fmt_len = len(fmt)
    while i < fmt_len:
        str_ = ""
        if fmt[i] == "%":
            j = i + 1
            if j < fmt_len:
                fmt_char = fmt[j]
                if fmt_char in _NEED_L10N:  # requires localization?
                    str_ = _thai_strftime(dt_obj, fmt_char, buddhist_era)
                elif fmt_char in _EXTENSIONS:
                    fmt_char_ext = fmt_char
                    k = j + 1
                    if k < fmt_len:
                        fmt_char = fmt[k]
                        if fmt_char in _NEED_L10N:
                            str_ = _thai_strftime(
                                dt_obj,
                                fmt_char,
                                buddhist_era,
                            )
                        else:
                            str_ = _std_strftime(dt_obj, fmt_char)

                        if fmt_char_ext == "-":
                            # GNU libc extension,
                            # no padding
                            if str_[0] and str_[0] in " 0":
                                str_ = str_[1:]
                        elif fmt_char_ext == "_":
                            # GNU libc extension,
                            # explicitly specify space (" ") for padding
                            if str_[0] and str_[0] == "0":
                                str_ = " " + str_[1:]
                        elif fmt_char_ext == "0":
                            # GNU libc extension,
                            # explicitly specify zero ("0") for padding
                            if str_[0] and str_[0] == " ":
                                str_ = "0" + str_[1:]
                        elif fmt_char_ext == "^":
                            # GNU libc extension,
                            # convert to upper case
                            str_ = str_.upper()
                        elif fmt_char_ext == "#":
                            # GNU libc extension,
                            # swap case - useful for %Z
                            str_ = str_.swapcase()
                        elif fmt_char_ext == "E":
                            # POSIX extension,
                            # uses the locale's alternative representation
                            # Not implemented yet
                            pass
                        elif fmt_char_ext == "O":
                            # POSIX extension,
                            # uses the locale's alternative numeric symbols
                            str_ = str_.translate(_HA_TH_DIGITS)
                        i = i + 1  # consume char after format char
                    else:
                        # format char at string's end has no meaning
                        str_ = fmt_char_ext
                else:  # not in _NEED_L10N nor _EXTENSIONS
                    # no known localization available, use Python's default
                    str_ = _std_strftime(dt_obj, fmt_char)

                i = i + 1  # consume char after "%"
            else:
                # % char at string's end has no meaning
                str_ = "%"
        else:
            str_ = fmt[i]

        thaidate_parts.append(str_)
        i = i + 1

    thaidate_text = "".join(thaidate_parts)

    if thai_digit:
        thaidate_text = thaidate_text.translate(_HA_TH_DIGITS)

    return thaidate_text


class Provider(DateParseTypeProvider):
    def date(
        self,
        pattern: str = "%-d %b %Y",
        end_datetime: Optional[DateParseType] = None,
        thai_digit: bool = False,
        buddhist_era: bool = True,
    ) -> str:
        """
        Get a date string between January 1, 1970 and now
        :param pattern: format
        :param end_datetime: datetime
        :param thai_digit: use Thai digit or not (default: False)
        :param buddhist_era: use Buddist era or not (default: True)
        :example: '08 พ.ย. 2563'
        :example: '๐๘ พ.ย. 2563' (thai_digit = True)
        :example: '8 พฤศิจกายน 2020' (pattern: str = "%-d %B %Y", buddhist_era = False)
        """
        return thai_strftime(
            self.date_time(end_datetime=end_datetime),
            pattern,
            thai_digit,
            buddhist_era,
        )

    def time(
        self,
        pattern: str = "%H:%M:%S",
        end_datetime: Optional[DateParseType] = None,
        thai_digit: bool = False,
    ) -> str:
        """
        Get a time string (24h format by default)
        :param pattern: format
        :param end_datetime: datetime
        :param thai_digit: use Thai digit or not (default: False)
        :example: '15:02:34'
        :example: '๑๕:๐๒:๓๔' (thai_digit = True)
        """
        return thai_strftime(
            self.date_time(end_datetime=end_datetime),
            pattern,
            thai_digit,
        )

    def century(self, thai_digit: bool = False, buddhist_era: bool = True) -> str:
        """
        :param thai_digi:t use Thai digit or not (default: False)
        :param buddhist:_era use Buddist era or not (default: True)
        :example: '20'
        """
        end_century = 22
        if buddhist_era:
            end_century = 26
        text = str(self.random_element(range(1, end_century)))
        if thai_digit:
            text = text.translate(_HA_TH_DIGITS)
        return text
