from typing import Optional

from .. import Provider as BankProvider


class Provider(BankProvider):
    """
    Implement bank provider for ``bn_BD`` locale.
    Sources:
        - https://wise.com/gb/swift-codes/BBHOBDDHXXX
        - https://www.banksbd.org/swift-codes.html
    """

    bban_format: str = "????#########"
    country_code = "BD"
    swift_location_codes = ("DH",)
    swift_branch_codes = (
        "ABBL",
        "AGBK",
        "ALAR",
        "ALFH",
        "BCBL",
        "BDDB",
        "BKBA",
        "BKSI",
        "BALB",
        "BRAK",
        "BBSH",
        "BSON",
        "CITI",
        "CCEY",
        "COYM",
        "CIBL",
        "DHBL",
        "DBBL",
        "EBLD",
        "EXBK",
        "FSEB",
        "FRMS",
        "HABB",
        "HSBC",
        "HVBK",
        "IFIC",
        "IBBL",
        "JAMU",
        "JANB",
        "MGBL",
        "MBLB",
        "MDBL",
        "MODH",
        "MTBL",
        "NGBL",
        "NBLB",
        "NBPA",
        "NCCL",
        "NRBD",
        "NRBB",
        "ONEB",
        "PRBL",
        "PRMR",
        "PUBA",
        "RUPB",
        "SJBL",
        "SOIV",
        "SBAC",
        "SEBD",
        "SDBL",
        "SCBL",
        "SBIN",
        "TTBL",
        "UBLD",
        "UCBL",
        "UTBL",
    )

    def swift8(self, use_dataset: bool = True) -> str:
        return super(self.__class__, self).swift8(use_dataset=use_dataset)

    def swift11(self, primary: bool = False, use_dataset: bool = True) -> str:
        return super(self.__class__, self).swift11(primary=primary, use_dataset=use_dataset)

    def swift(self, length: Optional[int] = None, primary: bool = False, use_dataset: bool = True) -> str:
        return super(self.__class__, self).swift(length=length, primary=primary, use_dataset=use_dataset)
