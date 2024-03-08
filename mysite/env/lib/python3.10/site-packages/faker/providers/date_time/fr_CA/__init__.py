from typing import Any

from ..fr_FR import Provider as FRFRProvider


class Provider(FRFRProvider):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
