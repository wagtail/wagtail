from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``fa_IR`` locale."""

    bban_format = "IR########################"
    country_code = "IR"
    swift_bank_codes = (
        "BEGN",
        "KESH",
        "BKMN",
        "BKBP",
        "CIYB",
        "BTOS",
        "IVBB",
        "KBID",
        "KIBO",
        "KHMI",
    )
    swift_location_codes = ("TH",)
    swift_branch_codes = ("BSH", "BCQ", "tIR", "tTH", "ATM", "BIC", "TIR", "ASR", "FOR")

    banks = (
        "بانکهای قرض الحسنه",
        "بانک ملّی ایران",
        "بانک اقتصاد نوین",
        "بانک قرض‌الحسنه مهر ایران",
        "بانک سپه",
        "بانک پارسیان",
        "بانک قرض‌الحسنه رسالت",
        "بانک صنعت و معدن",
        "بانک کارآفرین",
        "بانک کشاورزی",
        "بانک سامان",
        "بانک مسکن",
        "بانک سینا",
        "بانک توسعه صادرات ایران",
        "بانک خاور میانه",
        "بانک توسعه تعاون",
        "بانک شهر",
        "پست بانک ایران",
        "بانک دی",
        "بانک صادرات",
        "بانک ملت",
        "بانک تجارت",
        "بانک رفاه",
        "بانک حکمت ایرانیان",
        "بانک گردشگری",
        "بانک ایران زمین",
        "بانک قوامین",
        "بانک انصار",
        "بانک سرمایه",
        "بانک پاسارگاد",
        "بانک مشترک ایران-ونزوئلا",
    )

    def bank(self) -> str:
        """Generate a bank name."""
        return self.random_element(self.banks)
