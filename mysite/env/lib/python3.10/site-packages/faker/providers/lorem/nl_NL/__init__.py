from typing import Dict

from .. import Provider as LoremProvider
from ..nl_BE import Provider as LoremProviderNL_BE


class Provider(LoremProvider):
    """Implement lorem provider for ``nl_NL`` locale.

    Source: https://nl.wiktionary.org/wiki/WikiWoordenboek:Lijst_met_1000_basiswoorden
    """

    word_list = LoremProviderNL_BE.word_list
    parts_of_speech: Dict[str, tuple] = {}
