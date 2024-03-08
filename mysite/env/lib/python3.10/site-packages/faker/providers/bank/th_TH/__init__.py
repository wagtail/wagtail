from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``th_TH`` locale."""

    bban_format = "#" * 10
    country_code = "TH"
    swift_bank_codes = (
        "AIAC",
        "ANZB",
        "BKKB",
        "BAAB",
        "BOFA",
        "AYUD",
        "BKCH",
        "BOTH",
        "BNPA",
        "UBOB",
        "CITI",
        "CRES",
        "DEUT",
        "EXTH",
        "GSBA",
        "BHOB",
        "ICBK",
        "TIBT",
        "CHAS",
        "KASI",
        "KKPB",
        "KRTH",
        "LAHR",
        "ICBC",
        "MHCB",
        "OCBC",
        "DCBB",
        "SICO",
        "SMEB",
        "SCBL",
        "SMBC",
        "THBK",
        "HSBC",
        "TMBK",
        "UOVB",
    )
    swift_location_codes = (
        "BK",
        "B2",
        "BB",
        "BX",
        "2X",
    )
    swift_branch_codes = (
        "BKO",
        "BNA",
        "RYO",
        "CHB",
        "IBF",
        "SEC",
        "HDY",
        "CHM",
        "NAV",
        "XXX",
    )
