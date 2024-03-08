from faker.providers.bank import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``ro_RO`` locale."""

    country_code = "RO"
    bban_format = "????################"
    swift_bank_codes = (
        "NBOR",
        "ABNA",
        "BUCU",
        "ARBL",
        "MIND",
        "BPOS",
        "CARP",
        "RNCB",
        "BROM",
        "BITR",
        "BRDE",
        "BRMA",
        "BTRL",
        "DAFB",
        "MIRB",
        "CECE",
        "CITI",
        "CRCO",
        "FNNB",
        "EGNA",
        "BSEA",
        "EXIM",
        "UGBI",
        "HVBL",
        "INGB",
        "BREL",
        "CRDZ",
        "BNRB",
        "PIRB",
        "PORL",
        "MIRO",
        "RZBL",
        "RZBR",
        "ROIN",
        "WBAN",
        "TRFD",
        "TREZ",
        "BACX",
        "VBBU",
        "DARO",
    )
