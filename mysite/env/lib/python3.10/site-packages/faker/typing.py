import dataclasses
import sys

from datetime import date, datetime, timedelta
from typing import Sequence, Union

try:
    from typing import Literal  # type: ignore
except ImportError:
    from typing_extensions import Literal  # type: ignore

if sys.version_info >= (3, 9):
    from collections import OrderedDict as OrderedDictType
elif sys.version_info >= (3, 7, 2):
    from typing import OrderedDict as OrderedDictType
else:
    from typing_extensions import OrderedDict as OrderedDictType  # NOQA

DateParseType = Union[date, datetime, timedelta, str, int]
HueType = Union[str, float, int, Sequence[int]]
SexLiteral = Literal["M", "F"]
SeedType = Union[int, float, str, bytes, bytearray, None]


@dataclasses.dataclass
class Country:
    name: str
    timezones: Sequence[str]
    alpha_2_code: str
    alpha_3_code: str
    continent: str
    capital: str
