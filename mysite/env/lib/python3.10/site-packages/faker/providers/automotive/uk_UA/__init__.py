import random

from typing import Optional, Tuple

from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    plate_number_formats = ("####",)

    license_region_data = {
        "Crimea": (("AK", "KK", "TK", "MK"), "01"),
        "Kyiv": (("AA", "KA", "TT", "TA"), "11"),
        "Vinnytsia": (("AB", "KB", "MM", "OK"), "02"),
        "Volyn": (("AC", "KC", "SM", "TS"), "03"),
        "Dnipro": (("AE", "KE", "RR", "MI"), "04"),
        "Donetsk": (("AN", "KH", "TM", "MH"), "05"),
        "Kyiv_reg": (("AI", "KI", "TI", "ME"), "10"),
        "Zhytomyr": (("AM", "KM", "TM", "MV"), "06"),
        "Zakarpattia": (("AO", "KO", "MT", "MO"), "07"),
        "Zaporizhia": (("AR", "KR", "TR", "MR"), "08"),
        "IvanoFrankivsk": (("AT", "KT", "TO", "XS"), "09"),
        "Kirovohrad": (("BA", "NA", "XA", "EA"), "12"),
        "Luhansk": (("BB", "NV", "EE", "EV"), "13"),
        "Lviv": (("BS", "NS", "SS", "ES"), "14"),
        "Mykolaiv": (("BE", "NE", "XE", "XN"), "15"),
        "Odessa": (("BN", "NN", "OO", "EN"), "16"),
        "Poltava": (("BI", "NI", "XI", "EI"), "17"),
        "Rivne": (("BK", "NK", "XK", "EK"), "18"),
        "Sumy": (("BM", "NM", "XM", "EM"), "19"),
        "Ternopil": (("BO", "NO", "XO", "EO"), "20"),
        "Kharkiv": (("AX", "KX", "XX", "EX"), "21"),
        "Kherson": (("BT", "NT", "XT", "ET"), "22"),
        "Khmelnytsky": (("BX", "NX", "OX", "RX"), "23"),
        "Cherkasy": (("SA", "IA", "OA", "RA"), "24"),
        "Chernihiv": (("SV", "IV", "OV", "RV"), "25"),
        "Chernivtsi": (("SE", "IE", "OE", "RE"), "26"),
        "Sevastopol": (("SN", "IN", "ON", "RN"), "27"),
        "Nationwide": (("II", "ED", "DC", "DI", "PD"), "00"),
    }

    license_plate_suffix = (
        "AA",
        "BA",
        "CA",
        "EA",
        "HA",
        "IA",
        "KA",
        "MA",
        "OA",
        "PA",
        "TA",
        "XA",
        "AB",
        "BB",
        "CB",
        "EB",
        "HB",
        "IB",
        "KB",
        "MB",
        "OB",
        "PB",
        "TB",
        "XB",
        "AC",
        "BC",
        "BR",
        "EC",
        "HC",
        "IC",
        "KC",
        "MC",
        "OC",
        "PC",
        "TC",
        "XC",
        "AE",
        "BE",
        "CE",
        "EE",
        "HE",
        "IE",
        "KE",
        "ME",
        "OE",
        "PE",
        "TE",
        "XE",
        "AN",
        "BN",
        "CN",
        "EN",
        "HN",
        "IN",
        "KN",
        "MK",
        "ON",
        "PN",
        "TN",
        "XN",
        "AI",
        "BI",
        "CI",
        "EI",
        "HI",
        "II",
        "KI",
        "MI",
        "OI",
        "PI",
        "TI",
        "XI",
        "AK",
        "BK",
        "CK",
        "EK",
        "HK",
        "IK",
        "KK",
        "MK",
        "OK",
        "PK",
        "TK",
        "XK",
        "AM",
        "BM",
        "CM",
        "EM",
        "HM",
        "IM",
        "KM",
        "MM",
        "OM",
        "PM",
        "TM",
        "XM",
        "AO",
        "BO",
        "CO",
        "EO",
        "HO",
        "IO",
        "KO",
        "MO",
        "OO",
        "PO",
        "TO",
        "XO",
        "AP",
        "BP",
        "CP",
        "EP",
        "HP",
        "IP",
        "KP",
        "MP",
        "OP",
        "PP",
        "TP",
        "XP",
        "AT",
        "BT",
        "CT",
        "ET",
        "HT",
        "IT",
        "KT",
        "MT",
        "OT",
        "PT",
        "TT",
        "XT",
        "AX",
        "BX",
        "CX",
        "EX",
        "HX",
        "IX",
        "KX",
        "MX",
        "OX",
        "PX",
        "TX",
        "XX",
        "AY",
        "AZ",
        "BH",
        "BL",
        "BN",
        "BQ",
        "BR",
        "TU",
        "TV",
        "TY",
        "TZ",
    )

    vehicle_categories = ("A1", "A", "B1", "B", "C1", "C", "D1", "D", "BE", "C1E", "CE", "D1E", "DE", "T")

    def __get_random_region_code(self, region_name: Optional[str] = None) -> Tuple[str, str]:
        try:
            if region_name is None:
                region_name, _ = random.choice(list(self.license_region_data.items()))

            prefix, region_number = self.license_region_data[region_name]
            return random.choice(prefix), region_number
        except KeyError:
            region_names = ", ".join(self.license_region_data.keys())
            raise KeyError(f"Keys name must be only {region_names}")

    def license_plate(self, region_name: Optional[str] = None, temporary_plate: bool = False) -> str:
        """Generate a license plate.

        - If ``region_name`` is ``None`` (default), its value will be set to a random.
        - If ``region_name`` is ``Kyiv``, will use this region in build of license plates.
        - If ``temporary_plate`` is ``False`` (default), generate license plate AA0000AA format
        - If ``temporary_plate`` is ``True``, generate temporary plate format 01 AA0000
        01 - 27 it's region number

        :sample:
        :sample: region_name=None, temporary_plate=False
        :sample: region_name=None, temporary_plate=True
        :sample: region_name="Kyiv", temporary_plate=False
        :sample: region_name="Kyiv", temporary_plate=True
        """
        region, region_number = self.__get_random_region_code(region_name)
        if temporary_plate:
            return f"{region_number} {region}{self.plate_number()}"

        number = self.plate_number()
        series = self.plate_letter_suffix()
        return f"{region}{number}{series}"

    def plate_region_code(self, region_name: Optional[str] = None) -> str:
        """
        Generate plate region number

        :sample:
        :sample: region_name="Kyiv"
        """
        _, region_number = self.__get_random_region_code(region_name)
        return region_number

    def plate_letter_prefix(self, region_name: Optional[str] = None) -> str:
        """
        Generate a letter for license plates.

        :sample:
        :sample: region_name="Kyiv"
        """
        letters, _ = self.__get_random_region_code(region_name)
        return letters

    def plate_letter_suffix(self) -> str:
        """
        Generate a end letter for license plates.

        :sample:
        """
        return self.random_element(self.license_plate_suffix)

    def plate_number(self) -> str:
        """
        Generate a number for license plates.

        :sample:
        """
        return self.numerify(self.random_element(self.plate_number_formats))

    def diplomatic_license_plate(self) -> str:
        """
        Example: 'CDP 000'  or 'DP 000 000' or 'S 000 000' format

        :sample:
        """
        level = random.choice(("CDP", "DP", "S"))
        country_code = self.random_number(3, fix_len=True)
        car_number = self.random_number(3, fix_len=True)
        if level == "CDP":
            return f"{level} {country_code}"
        return f"{level} {country_code} {car_number}"

    def vehicle_category(self) -> str:
        """
        Generate a vehicle category code for license plates.

        :sample:
        """
        return self.random_element(self.vehicle_categories)
