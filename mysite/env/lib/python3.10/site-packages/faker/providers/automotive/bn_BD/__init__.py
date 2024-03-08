from faker.providers.person.bn_BD import translate_to_bengali_digits

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``bn_BD`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_Bangladesh
    """

    # noinspection DuplicatedCode
    cities = (
        "বরগুনা",
        "বরিশাল",
        "বরিশাল মেট্রো",
        "ভোলা",
        "বান্দরবান",
        "ব্রাহ্মণবাড়িয়া",
        "বাগেরহাট",
        "বগুড়া",
        "চাঁদপুর",
        "চট্টগ্রাম",
        "চট্ট মেট্রো",
        "কুমিল্লা",
        "কক্সবাজার",
        "চুয়াডাঙ্গা",
        "ঢাকা",
        "ঢাকা মেট্রো",
        "দিনাজপুর",
        "ফরিদপুর",
        "ফেনী",
        "গাজীপুর",
        "গোপালগঞ্জ",
        "গাইবান্ধা",
        "হবিগঞ্জ",
        "ঝালকাঠি",
        "যশোর",
        "ঝিনাইদহ",
        "জামালপুর",
        "জয়পুরহাট",
        "খাগড়াছড়ি",
        "কিশোরগঞ্জ",
        "খুলনা",
        "খুলনা মেট্রো",
        "কুষ্টিয়া",
        "কুড়িগ্রাম",
        "লক্ষ্মীপুর",
        "লালমনিরহাট",
        "মাদারীপুর",
        "মানিকগঞ্জ",
        "মুন্সীগঞ্জ",
        "মাগুরা",
        "মেহেরপুর",
        "ময়মনসিংহ",
        "মৌলভীবাজার",
        "নোয়াখালী",
        "নারায়ণগঞ্জ",
        "নরসিংদী",
        "নড়াইল",
        "নেত্রকোণা",
        "নওগাঁ",
        "নাটোর",
        "চাঁপাইনবাবগঞ্জ",
        "নীলফামারী",
        "পটুয়াখালী",
        "পিরোজপুর",
        "পাবনা",
        "পঞ্চগড়",
        "রাঙ্গামাটি",
        "রাজবাড়ী",
        "রাজশাহী",
        "রাজ মেট্রো",
        "রংপুর",
        "শরীয়তপুর",
        "সাতক্ষীরা",
        "শেরপুর",
        "সিরাজগঞ্জ",
        "সুনামগঞ্জ",
        "সিলেট",
        "সিলেট মেট্রো",
        "টাঙ্গাইল",
        "ঠাকুরগাঁও",
    )

    vehicle_category_letters = (
        "অ",
        "ই",
        "উ",
        "এ",
        "ক",
        "খ",
        "গ",
        "ঘ",
        "ঙ",
        "চ",
        "ছ",
        "জ",
        "ঝ",
        "ত",
        "থ",
        "ঢ",
        "ড",
        "ট",
        "ঠ",
        "দ",
        "ধ",
        "ন",
        "প",
        "ফ",
        "ব",
        "ভ",
        "ম",
        "য",
        "র",
        "ল",
        "শ",
        "স",
        "হ",
    )

    vehicle_category_numbers = (
        "১১",
        "১২",
        "১৩",
        "১৪",
        "১৫",
        "১৬",
        "১৭",
        "১৮",
        "১৯",
        "২০",
        "২১",
        "২২",
        "২৩",
        "২৪",
        "২৫",
        "২৬",
        "২৭",
        "২৮",
        "২৯",
        "৩০",
        "৩১",
        "৩২",
        "৩৩",
        "৩৪",
        "৩৫",
        "৩৬",
        "৩৭",
        "৩৮",
        "৩৯",
        "৪০",
        "৪১",
        "৪২",
        "৪৩",
        "৪৪",
        "৪৫",
        "৪৬",
        "৪৭",
        "৪৮",
        "৪৯",
        "৫০",
        "৫১",
        "৫২",
        "৫৩",
        "৫৪",
        "৫৫",
        "৫৬",
        "৫৭",
        "৫৮",
        "৫৯",
        "৬০",
        "৬১",
        "৬২",
        "৬৩",
        "৬৪",
        "৬৫",
        "৬৬",
        "৬৭",
        "৬৮",
        "৬৯",
        "৭০",
        "৭১",
        "৭২",
        "৭৩",
        "৭৪",
        "৭৫",
        "৭৬",
        "৭৭",
        "৭৮",
        "৭৯",
        "৮০",
        "৮১",
        "৮২",
        "৮৩",
        "৮৪",
        "৮৫",
        "৮৬",
        "৮৭",
        "৮৮",
        "৮৯",
        "৯০",
        "৯১",
        "৯২",
        "৯৩",
        "৯৪",
        "৯৫",
        "৯৬",
        "৯৭",
        "৯৮",
        "৯৯",
    )

    vehicle_serial_number_formats = ("%###",)

    license_plate_formats = (
        "{{city_name}}-{{vehicle_category_letter}} {{vehicle_category_number}}-{{vehicle_serial_number}}",
    )

    def city_name(self) -> str:
        """
        :example: 'ঢাকা মেট্রো'
        """
        return self.random_element(self.cities)

    def vehicle_category_letter(self) -> str:
        """
        :example: 'ব'
        """
        return self.random_element(self.vehicle_category_letters)

    def vehicle_category_number(self) -> str:
        """
        :example: '১১'
        """
        return self.random_element(self.vehicle_category_numbers)

    def vehicle_serial_number(self) -> str:
        """
        Generate a 4 digits vehicle serial number.
        :example: '৫৪৩২'
        """
        return translate_to_bengali_digits(self.numerify(self.random_element(self.vehicle_serial_number_formats)))

    def license_plate(self) -> str:
        """
        Generate a license plate.
        :example: 'বরিশাল-ভ ৬৭-৪৫৯৩'
        """
        pattern: str = self.random_element(self.license_plate_formats)
        return self.generator.parse(pattern)
