from .. import Provider as PersonProvider


def translate_to_bengali_digits(en_digit: str = "0") -> str:
    """
    Translate any English string containing digits to corresponding Bengali digits.
    :example: '9786' to '৯৭৮৬'
    """
    english_to_bengali_digits_map = {
        "0": "০",
        "1": "১",
        "2": "২",
        "3": "৩",
        "4": "৪",
        "5": "৫",
        "6": "৬",
        "7": "৭",
        "8": "৮",
        "9": "৯",
    }
    bn_digit = ""
    for char in en_digit:
        bn_digit = bn_digit + english_to_bengali_digits_map.get(char, char)
    return bn_digit


class Provider(PersonProvider):
    """Implement person provider for ``bn_BD`` locale."""

    prefixes = (
        "ইঞ্জিঃ",
        "ডাঃ",
        "ডঃ",
    )

    prefixes_male = (
        "জনাব",
        "মিঃ",
        "মৃতঃ",
    ) + prefixes

    prefixes_female = (
        "জনাবা",
        "মিসঃ",
        "মিসেস",
        "মৃতাঃ",
    ) + prefixes

    suffixes = (
        "অবঃ",
        "এমএসসি",
        "এমডি",
        "ডিডিএস",
        "ডিভিএম",
        "পিএইচডি",
        "বিএসসি",
    )

    language_names = (
        "আফার",
        "আবখাজিয়ান",
        "আবেস্তান",
        "আফ্রিকান",
        "আকান",
        "আমহারিক",
        "আরাগোনিজ",
        "আরবি",
        "অসমীয়া",
        "অ্যাভারিক",
        "আয়মারা",
        "আজারবাইজানীয়",
        "বাশকির",
        "বেলারুশিয়ান",
        "বুলগেরিয়ান",
        "বিহারী ভাষা" "বিসলামা",
        "বামবারা",
        "বাংলা",
        "তিব্বতি",
        "ব্রেটন",
        "বসনীয়",
        "কাতালান",
        "চেচেন",
        "চামোরো",
        "করসিকান",
        "ক্রি",
        "চেক",
        "চার্চ স্লাভিক",
        "চুভাশ",
        "ওয়েলশ",
        "ড্যানিশ",
        "জার্মান",
        "দিভেহি",
        "জংখা",
        "ইউ",
        "গ্রীক",
        "ইংরেজি",
        "এসপেরান্তো",
        "স্পেনীয়",
        "এস্তোনিয়ান",
        "বাস্ক",
        "ফারসি",
        "ফুলাহ",
        "ফিনিশ",
        "ফিজিয়ান",
        "ফেরোজ",
        "ফরাসি",
        "পশ্চিম ফ্রিসিয়ান",
        "আইরিশ",
        "গেলিক",
        "গ্যালিশিয়ান",
        "গুয়ারানি",
        "গুজরাটি",
        "ম্যানক্স",
        "হাউসা",
        "হিব্রু",
        "হিন্দি",
        "হিরি মোটু",
        "ক্রোয়েশিয়ান",
        "হাইতিয়ান",
        "হাঙ্গেরিয়ান",
        "আর্মেনিয়ান",
        "হেরো",
        "ইন্টারলিঙ্গুয়া",
        "ইন্দোনেশিয়ান",
        "আন্তর্ভাষা",
        "ইগবো",
        "সিচুয়ান ই",
        "ইনুপিয়াক",
        "আমি করি",
        "আইসল্যান্ডিক",
        "ইতালীয়",
        "ইনুকটিটুট",
        "জাপানি",
        "জাভানিজ",
        "জর্জিয়ান",
        "কঙ্গো",
        "কিকুয়ু",
        "কুয়ানিয়ামা",
        "কাজাখ",
        "কালাল্লিসুত",
        "সেন্ট্রাল খেমার",
        "কন্নড়",
        "কোরিয়ান",
        "কানুরি",
        "কাশ্মীরি",
        "কুর্দি",
        "কোমি",
        "কর্নিশ",
        "কিরঘিজ",
        "ল্যাটিন",
        "লাক্সেমবার্গিশ",
        "গান্ডা",
        "লিম্বুরগান",
        "লিঙ্গালা",
        "লাও",
        "লিথুয়ানিয়ান",
        "লুবা-কাটাঙ্গা",
        "লাটভিয়ান",
        "মালাগাসি",
        "মার্শালিজ",
        "মাওরি",
        "ম্যাসিডোনিয়ান",
        "মালয়ালম",
        "মঙ্গোলিয়ান",
        "মারাঠি",
        "মালয়",
        "মালটিজ",
        "বর্মী",
        "নাউরু",
        "উত্তর নেদেবেলে",
        "নেপালি",
        "এনডোঙ্গা",
        "ডাচ",
        "নরওয়েজিয়ান নাইনরস্ক",
        "নরওয়েজীয়",
        "দক্ষিণ নেদেবেলে",
        "নাভাজো",
        "চিচেওয়া",
        "অক্সিটান",
        "ওজিবওয়া",
        "ওরোমো",
        "ওড়িয়া",
        "ওসেশিয়ান",
        "পাঞ্জাবি",
        "পালি",
        "পোলিশ",
        "ধাক্কা",
        "পর্তুগীজ",
        "কেচুয়া",
        "রোমানশ",
        "রুন্ডি",
        "রোমানিয়ান",
        "রাশিয়ান",
        "কিনিয়ারওয়ান্ডা",
        "সংস্কৃত",
        "সার্ডিনিয়ান",
        "সিন্ধি",
        "উত্তর সামি",
        "সাঙ্গো",
        "সিংহল",
        "স্লোভাক",
        "স্লোভেনীয়",
        "সামোয়ান",
        "শোনা",
        "সোমালি",
        "আলবেনিয়ান",
        "সার্বিয়ান",
        "স্বাতী",
        "সোথো, দক্ষিণ",
        "সুদানিজ",
        "সুইডিশ",
        "সোয়াহিলি",
        "তামিল",
        "তেলেগু",
        "তাজিক",
        "থাই",
        "টাইগ্রিনিয়া",
        "তুর্কমেন",
        "তাগালগ",
        "সোয়ানা",
        "টোঙ্গা",
        "তুর্কি",
        "সোঙ্গা",
        "তাতার",
        "টুই",
        "তাহিতিয়ান",
        "উইঘুর",
        "ইউক্রেনীয়",
        "উর্দু",
        "উজবেক",
        "ভেন্দা",
        "ভিয়েতনামী",
        "ওয়ালুন",
        "ওলোফ",
        "জোসা",
        "ইদ্দিশ",
        "ইয়োরুবা",
        "ঝুয়াং",
        "চীনা",
        "জুলু",
    )

    first_names_male_common = (
        "অর্ক",
        "আকাশ",
        "আরিয়ান",
        "আদি",
        "অভিষেক",
        "অভি",
        "আনন্দ",
        "আবির",
        "ইমন",
        "চয়ন",
        "চঞ্চল",
        "তন্ময়",
        "তনয়",
        "তুষার",
        "নয়ন",
        "প্রান্ত",
        "প্রিতম",
        "প্রিয়ম",
        "প্রিয়",
        "প্রত্যয়",
        "বাদল",
        "মিলন",
        "রাহুল",
        "রোহিত",
        "লিটন",
        "শাওন",
        "শান্ত",
        "শুভ",
        "সজীব",
        "রাজ",
        "রাজু",
        "রুদ্র",
    )

    first_names_male_hinduism = (
        "অর্ঘ্য",
        "অশোক",
        "অজিত",
        "অর্ণব",
        "অক্ষয়",
        "অমল",
        "অজয়",
        "আশীষ",
        "আশুতোষ",
        "আয়ুষ",
        "কুনাল",
        "জয়ন্ত",
        "জয়দীপ",
        "জগদীশ",
        "প্রদ্যুম্ন",
        "প্রদীপ",
        "প্রশান্ত",
        "বিনয়",
        "বিরাট",
        "মৃনাল",
        "মৃত্যুঞ্জয়",
        "মনোজ",
        "শেখর",
        "সুশান্ত",
        "সৌমিক",
        "সৌম্য",
    )

    first_names_male_islamic = (
        "আবু",
        "আতাহার",
        "আজাদ",
        "আসাদ",
        "আনিস",
        "আজম",
        "আব্বাস",
        "ইকবাল",
        "ইউসুফ",
        "ইশতিয়াক",
        "ইমতিয়াজ",
        "ইজাজ",
        "এনামুল",
        "একরামুল",
        "কাফি",
        "করিম",
        "তামিম",
        "নাদিম",
        "নাইম",
        "বাকের",
        "বাসির",
        "মুনতাসির",
        "মুনতাকিম",
        "মোস্তাফিজ",
        "মুশফিক",
        "রায়হান",
        "রহিম",
        "রাশেদ",
        "রাসেল",
        "রাশেদুল",
        "শাহাবাজ",
        "শাহজাহান",
        "শহিদুল",
        "সাবের",
        "সাব্বির",
    )

    first_names_female_common = (
        "অর্পিতা",
        "অঞ্জনা",
        "অহনা",
        "অন্তরা",
        "অর্না",
        "অনন্যা",
        "আরিয়া",
        "আশা",
        "আলিয়া",
        "ইশিতা",
        "কেয়া",
        "কবিতা",
        "কাজল",
        "খুশি",
        "ডলি",
        "জনা",
        "নন্দিতা",
        "নিশিতা",
        "প্রীতি",
        "প্রিয়তি",
        "প্রিয়াঙ্কা",
        "প্রিয়া",
        "বাঁধন",
        "বৃষ্টি",
        "বিনা",
        "বিপাশা",
        "মিথিলা",
        "মিষ্টি",
        "মিলা",
        "মিনা",
        "মিম",
        "রিনা",
        "লতা",
        "শ্রাবনী",
        "শ্রাবন্তী",
        "সুরভি",
    )

    first_names_female_hinduism = (
        "অদৃতা",
        "অনিন্দিতা",
        "অলোকা",
        "অদিতি",
        "আমায়া",
        "আরাধ্যা",
        "আরুণি",
        "আশালতা",
        "আশ্বিনী",
        "আয়ুশি",
        "ঋষিতা",
        "ঈশানি",
        "কাবেরি",
        "দূর্গা",
        "বিদ্যা",
        "মাধুরী",
        "মাধু",
        "হৈমন্তী",
        "শুভশ্রী",
    )

    first_names_female_islamic = (
        "আক্তারা",
        "আফিয়া",
        "আসিফা",
        "আফিফা",
        "আফসানা",
        "আয়েশা",
        "জোবায়দা",
        "তাসফিয়া",
        "তাসনিম",
        "তামান্না",
        "নুসরাত",
        "ফৌজিয়া",
        "ফারিহা",
        "মেহজাবিন",
        "মোনালিসা",
        "মালিহা",
        "রাজিয়া",
        "রোজিনা",
        "শারমিন",
        "সানজিদা",
        "সুমাইয়া",
    )

    last_names_common = (
        "চৌধুরী",
        "তালুকদার",
        "প্রামানিক",
        "বিশ্বাস",
        "মৃধা",
        "মজুমদার",
        "মোড়ল",
        "মন্ডল",
        "সরকার",
        "সিনহা",
    )

    last_names_hinduism = (
        "আচার্য্য",
        "কুমার",
        "কান্ত",
        "গাঙ্গুলি",
        "গঙ্গোপাধ্যায়",
        "ঘোষ",
        "চ্যাটার্জি",
        "চট্টোপাধ্যায়",
        "চন্দ্র",
        "ঠাকুর",
        "দত্ত",
        "দাস",
        "দেব",
        "দে",
        "দাশগুপ্তা",
        "পাল",
        "পোদ্দার",
        "পাণ্ডে",
        "প্রধান",
        "ব্যানার্জি",
        "বন্দোপাধ্যায়",
        "বোস",
        "বসু",
        "বর্মন",
        "বাগচী",
        "মুখার্জি",
        "মিশ্র",
        "মিত্র",
        "যাদব",
        "শুক্লা",
        "সাহা",
        "সিং",
        "সেন",
        "রায়",
        "রাও",
    )

    last_names_islamic = (
        "আলি",
        "আক্তার",
        "আওয়াল",
        "আলম",
        "আবদুল্লাহ",
        "ইসলাম",
        "উদ্দিন",
        "কাদের",
        "খান",
        "জামান",
        "মিঞা",
        "হোসাইন",
        "হক",
        "হুরাইরা",
        "হাকিম",
        "রহমান",
    )

    last_names_female_islamic = (
        "আরা",
        "খানম",
        "খাতুন",
        "জাহান",
        "তাবাসসুম",
        "বেগম",
        "সুলতানা",
    ) + last_names_islamic

    formats_male = [
        "{{first_name_male_common}} {{last_name_common}}",
        "{{first_name_male_hinduism}} {{last_name_common}}",
        "{{first_name_male_common}} {{last_name_hinduism}}",
        "{{first_name_male_hinduism}} {{last_name_hinduism}}",
        "{{first_name_male_islamic}} {{last_name_common}}",
        "{{first_name_male_common}} {{last_name_islamic}}",
        "{{first_name_male_islamic}} {{last_name_islamic}}",
    ]

    formats_female = [
        "{{first_name_female_common}} {{last_name_common}}",
        "{{first_name_female_hinduism}} {{last_name_common}}",
        "{{first_name_female_common}} {{last_name_hinduism}}",
        "{{first_name_female_hinduism}} {{last_name_hinduism}}",
        "{{first_name_female_islamic}} {{last_name_common}}",
        "{{first_name_female_common}} {{last_name_female_islamic}}",
        "{{first_name_female_islamic}} {{last_name_female_islamic}}",
    ]

    formats = formats_male + formats_female

    first_names_male = first_names_male_common + first_names_male_hinduism + first_names_male_islamic
    first_names_female = first_names_female_common + first_names_female_hinduism + first_names_female_islamic
    first_names = first_names_male + first_names_female

    last_names_male = last_names_common + last_names_hinduism + last_names_islamic
    last_names_female = last_names_common + last_names_hinduism + last_names_female_islamic
    last_names = last_names_male + last_names_female

    def first_name_male_common(self) -> str:
        """
        Return religiously unbiased male first name.
        :example: 'প্রিতম'
        """
        return self.random_element(self.first_names_male_common)

    def first_name_male_hinduism(self) -> str:
        """
        Return Hindu religion based male first name.
        :example: 'অশোক'
        """
        return self.random_element(self.first_names_male_hinduism)

    def first_name_male_islamic(self) -> str:
        """
        Return Islam religion based male first name.
        :example: 'ইকবাল'
        """
        return self.random_element(self.first_names_male_islamic)

    def first_name_female_common(self) -> str:
        """
        Return religiously unbiased female first name.
        :example: 'অর্পিতা'
        """
        return self.random_element(self.first_names_female_common)

    def first_name_female_hinduism(self) -> str:
        """
        Return Hindu religion based female first name.
        :example: 'দূর্গা'
        """
        return self.random_element(self.first_names_female_hinduism)

    def first_name_female_islamic(self) -> str:
        """
        Return Islam religion based female first name.
        :example: 'মেহজাবিন'
        """
        return self.random_element(self.first_names_male_islamic)

    def last_name_common(self) -> str:
        """
        Return religiously and gender unbiased last name.
        :example: 'চৌধুরী'
        """
        return self.random_element(self.last_names_common)

    def last_name_hinduism(self) -> str:
        """
        Return gender unbiased Hindu religion based last name.
        :example: 'দত্ত'
        """
        return self.random_element(self.last_names_hinduism)

    def last_name_islamic(self) -> str:
        """
        Return gender unbiased Islam religion based last name.
        :example: 'আলি'
        """
        return self.random_element(self.last_names_islamic)

    def last_name_female_islamic(self) -> str:
        """
        Return Islam religion based female last name.
        :example: 'খাতুন'
        """
        return self.random_element(self.last_names_female_islamic)
