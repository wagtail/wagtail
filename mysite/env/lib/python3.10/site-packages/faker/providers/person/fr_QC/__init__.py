import warnings

from typing import Any

from ..fr_CA import Provider as FRCAProvider


class Provider(FRCAProvider):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn("fr_QC locale is deprecated. Please use fr_CA.")
        super().__init__(*args, **kwargs)
