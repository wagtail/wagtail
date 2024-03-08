from collections import OrderedDict

from .. import CreditCard
from .. import Provider as CreditCardProvider


class Provider(CreditCardProvider):
    """Implement credit card provider for ``fa_IR`` locale.

    For all methods that take ``card_type`` as an argument, a random card type
    will be used if the supplied value is ``None``. The list of valid card types
    includes ``'ansar'``, ``'bim'``, ``'day'``, ``'eghtesad_novin'``,
    ``'ghavamin'``, ``'hekmat'``, ``'iran_zamin'``, ``'kar_afarin'``,
    ``'keshavarzi'``, ``'kosar'``, ``'maskan'``, ``'mehre_ghtesad'``,
    ``'meli'``, ``'mellal'``, ``'mellat'``, ``'parsian'``, ``'pasargad'``,
    ``'post_bank'``, ``'refah'``, ``'saderat'``, ``'saman'``, ``'sarmayeh'``,
    ``'sepah'``, ``'shahr'``, ``'sina'``, ``'tat'``, ``'tejarat'``, ``'tose'``,
    and ``'tourism_bank'``.

    Sources:

    - https://way2pay.ir/21653
    """

    prefix_ansar = ["627381"]
    prefix_iran_zamin = ["505785"]
    prefix_hekmat = ["636949"]
    prefix_keshavarzi = ["603770"]
    prefix_shahr = ["502806"]
    prefix_mehr_eghtesad = ["606373"]
    prefix_sarmayeh = ["639607"]
    prefix_post_bank = ["627760"]
    prefix_tose = ["628157"]
    prefix_eghtesad_novin = ["627412"]
    prefix_meli = ["603799"]
    prefix_pasargad = ["502229"]
    prefix_tourism_bank = ["505416"]
    prefix_ghavamin = ["639599"]
    prefix_day = ["502938"]
    prefix_mellat = ["610433"]
    prefix_tejarat = ["585983"]
    prefix_moasse_mellal = ["606256"]
    prefix_saman_bank = ["621986"]
    prefix_kosar = ["505801"]
    prefix_refah = ["589463"]
    prefix_saderat = ["603761"]
    prefix_tat = ["621986"]
    prefix_sina = ["639346"]
    prefix_kar_afarin = ["627488"]
    prefix_sepah = ["589210"]
    prefix_maskan = ["628023"]
    prefix_parsian = ["622106"]
    prefix_bim = ["627961"]

    credit_card_types = OrderedDict(
        (
            ("ansar", CreditCard("انصار", prefix_ansar, 16, security_code="CVV2")),
            (
                "iran_zamin",
                CreditCard("ایران زمین", prefix_iran_zamin, 16, security_code="CVV2"),
            ),
            ("hekmat", CreditCard("حکمت", prefix_hekmat, 16, security_code="CVV2")),
            (
                "keshavarzi",
                CreditCard("کشاورزی", prefix_keshavarzi, 16, security_code="CVV2"),
            ),
            ("shahr", CreditCard("شهر", prefix_shahr, 16, security_code="CVV2")),
            (
                "mehre_ghtesad",
                CreditCard("مهراقتصاد", prefix_mehr_eghtesad, 16, security_code="CVV2"),
            ),
            (
                "sarmayeh",
                CreditCard("سرمایه", prefix_sarmayeh, 16, security_code="CVV2"),
            ),
            (
                "post_bank",
                CreditCard("پست بانک", prefix_post_bank, 16, security_code="CVV2"),
            ),
            ("tose", CreditCard("توسعه", prefix_tose, 16, security_code="CVV2")),
            (
                "eghtesad_novin",
                CreditCard("اقتصاد نوین", prefix_eghtesad_novin, 16, security_code="CVV2"),
            ),
            ("meli", CreditCard("ملی", prefix_meli, 16, security_code="CVV2")),
            (
                "pasargad",
                CreditCard("پاسارگاد", prefix_pasargad, 16, security_code="CVV2"),
            ),
            (
                "tourism_bank",
                CreditCard("گردشگری", prefix_tourism_bank, 16, security_code="CVV2"),
            ),
            (
                "ghavamin",
                CreditCard("قوامین", prefix_ghavamin, 16, security_code="CVV2"),
            ),
            ("day", CreditCard("دی", prefix_day, 16, security_code="CVV2")),
            ("mellat", CreditCard("ملت", prefix_mellat, 16, security_code="CVV2")),
            ("tejarat", CreditCard("تجارت", prefix_tejarat, 16, security_code="CVV2")),
            (
                "mellal",
                CreditCard("ملل", prefix_moasse_mellal, 16, security_code="CVV2"),
            ),
            ("saman", CreditCard("سامان", prefix_saman_bank, 16, security_code="CVV2")),
            ("kosar", CreditCard("کوثر", prefix_kosar, 16, security_code="CVV2")),
            ("refah", CreditCard("رفاه", prefix_refah, 16, security_code="CVV2")),
            ("saderat", CreditCard("صادرات", prefix_saderat, 16, security_code="CVV2")),
            ("tat", CreditCard("تات", prefix_tat, 16, security_code="CVV2")),
            ("sina", CreditCard("سینا", prefix_sina, 16, security_code="CVV2")),
            (
                "kar_afarin",
                CreditCard("کار آفرین", prefix_kar_afarin, 16, security_code="CVV2"),
            ),
            ("sepah", CreditCard("سپه", prefix_sepah, 16, security_code="CVV2")),
            ("maskan", CreditCard("مسکن", prefix_maskan, 16, security_code="CVV2")),
            (
                "parsian",
                CreditCard("پارسیان", prefix_parsian, 16, security_code="CVV2"),
            ),
            ("bim", CreditCard("صنعت و معدن", prefix_bim, 16, security_code="CVV2")),
        )
    )
