from collections import OrderedDict

from ..th import Provider as AddressProvider


class Provider(AddressProvider):
    street_name_formats = ("{{street_prefix}}{{last_name}}",)
    street_address_formats = ("{{building_number}} {{street_name}}",)

    address_formats = OrderedDict(
        (
            (
                "{{street_address}} {{tambon}} {{amphoe}} {{province}} {{postcode}}",
                50.0,
            ),
            (
                "{{street_address}} ตำบล{{tambon}} อำเภอ{{amphoe}} {{province}} {{postcode}}",
                50.0,
            ),
            (
                "{{street_address}} ต.{{tambon}} อ.{{amphoe}} {{province}} {{postcode}}",
                50.0,
            ),
            (
                "{{street_address}} ต.{{tambon}} อ.{{amphoe}} จ.{{province}} {{postcode}}",
                40.0,
            ),
            ("{{street_address}} อำเภอ{{amphoe}} {{province}} {{postcode}}", 30.0),
            ("{{street_address}} อ.{{amphoe}} {{province}} {{postcode}}", 30.0),
            ("{{street_address}} {{amphoe}} {{province}} {{postcode}}", 30.0),
            ("{{street_address}} {{tambon}} {{province}} {{postcode}}", 15.0),
            ("{{street_address}} {{amphoe}} จ.{{province}} {{postcode}}", 15.0),
            ("{{street_address}} {{tambon}} จ.{{province}} {{postcode}}", 15.0),
            ("{{street_address}} อ.{{amphoe}} จ.{{province}} {{postcode}}", 15.0),
            ("{{street_address}} ต.{{tambon}} จ.{{province}} {{postcode}}", 15.0),
            (
                "{{street_address}} อำเภอ{{amphoe}} จังหวัด{{province}} {{postcode}}",
                15.0,
            ),
            (
                "{{street_address}} ตำบล{{tambon}} อำเภอ{{amphoe}} จังหวัด{{province}} {{postcode}}",
                10.0,
            ),
            ("{{street_address}} {{province}} {{postcode}}", 15.0),
            ("{{street_address}} ต.{{tambon}} อ.{{amphoe}} {{province}}", 15.0),
            ("{{street_address}} ต.{{tambon}} อ.{{amphoe}} จ.{{province}}", 15.0),
            (
                "{{street_address}} ตำบล{{tambon}} จังหวัด{{province}} {{postcode}}",
                10.0,
            ),
            (
                "{{building_number}} ต.{{tambon}} อ.{{amphoe}} {{province}} {{postcode}}",
                10.0,
            ),
            (
                "{{building_number}} หมู่บ้าน{{first_name}} {{amphoe}} {{province}} {{postcode}}",
                10.0,
            ),
        )
    )

    # city names are actual city municipalities in Thailand
    # source: Wikipedia: https://th.wikipedia.org/wiki/เทศบาลนครในประเทศไทย
    city_formats = ("{{city_name}}",)
    cities = (
        "กรุงเทพมหานคร",
        "นนทบุรี",
        "ปากเกร็ด",
        "หาดใหญ่",
        "เจ้าพระยาสุรศักดิ์",
        "สุราษฎร์ธานี",
        "อุดรธานี",
        "เชียงใหม่",
        "นครราชสีมา",
        "พัทยา",
        "ขอนแก่น",
        "นครศรีธรรมราช",
        "แหลมฉบัง",
        "รังสิต",
        "นครสวรรค์",
        "ภูเก็ต",
        "เชียงราย",
        "อุบลราชธานี",
        "นครปฐม",
        "เกาะสมุย",
        "สมุทรสาคร",
        "พิษณุโลก",
        "ระยอง",
        "สงขลา",
        "ยะลา",
        "ตรัง",
        "อ้อมน้อย",
        "สกลนคร",
        "ลำปาง",
        "สมุทรปราการ",
        "พระนครศรีอยุธยา",
        "แม่สอด",
    )

    building_number_formats = (
        "###",
        "##",
        "#",
        "###/#",
        "###/##",
        "##/#",
        "##/##",
        "#/#",
        "## หมู่ #",
        "## หมู่ ##",
    )

    street_prefixes = OrderedDict(
        (
            ("ถนน", 0.5),
            ("ถ.", 0.4),
            ("ซอย", 0.02),
            ("ซ.", 0.02),
        )
    )

    postcode_formats = (
        # as per https://en.wikipedia.org/wiki/Postal_codes_in_Thailand
        "1###0",
        "2###0",
        "3###0",
        "4###0",
        "5###0",
        "6###0",
        "7###0",
        "8###0",
        "9###0",
    )

    provinces = (
        "กระบี่",
        "กรุงเทพมหานคร",
        "กรุงเทพ",
        "กรุงเทพฯ",
        "กทม.",
        "กาญจนบุรี",
        "กาฬสินธุ์",
        "กำแพงเพชร",
        "ขอนแก่น",
        "จันทบุรี",
        "ฉะเชิงเทรา",
        "ชลบุรี",
        "ชัยนาท",
        "ชัยภูมิ",
        "ชุมพร",
        "เชียงราย",
        "เชียงใหม่",
        "ตรัง",
        "ตราด",
        "ตาก",
        "นครนายก",
        "นครปฐม",
        "นครพนม",
        "นครราชสีมา",
        "นครศรีธรรมราช",
        "นครสวรรค์",
        "นนทบุรี",
        "นราธิวาส",
        "น่าน",
        "บึงกาฬ",
        "บุรีรัมย์",
        "ปทุมธานี",
        "ประจวบคีรีขันธ์",
        "ปราจีนบุรี",
        "ปัตตานี",
        "พระนครศรีอยุธยา",
        "พะเยา",
        "พังงา",
        "พัทลุง",
        "พิจิตร",
        "พิษณุโลก",
        "เพชรบุรี",
        "เพชรบูรณ์",
        "แพร่",
        "ภูเก็ต",
        "มหาสารคาม",
        "มุกดาหาร",
        "แม่ฮ่องสอน",
        "ยโสธร",
        "ยะลา",
        "ร้อยเอ็ด",
        "ระนอง",
        "ระยอง",
        "ราชบุรี",
        "ลพบุรี",
        "ลำปาง",
        "ลำพูน",
        "เลย",
        "ศรีสะเกษ",
        "สกลนคร",
        "สงขลา",
        "สตูล",
        "สมุทรปราการ",
        "สมุทรสงคราม",
        "สมุทรสาคร",
        "สระแก้ว",
        "สระบุรี",
        "สิงห์บุรี",
        "สุโขทัย",
        "สุพรรณบุรี",
        "สุราษฎร์ธานี",
        "สุรินทร์",
        "หนองคาย",
        "หนองบัวลำภู",
        "อ่างทอง",
        "อำนาจเจริญ",
        "อุดรธานี",
        "อุตรดิตถ์",
        "อุทัยธานี",
        "อุบลราชธานี",
    )

    amphoes = (
        "เกษตรสมบูรณ์",
        "แก้งคร้อ",
        "คอนสวรรค์",
        "คอนสาร",
        "ซับใหญ่",
        "เทพสถิต",
        "เนินสง่า",
        "บ้านเขว้า",
        "บ้านแท่น",
        "บำเหน็จณรงค์",
        "หนองบัวโคก",
        "ภักดีชุมพล",
        "ภูเขียว",
        "หนองบัวแดง",
        "หนองบัวระเหว",
        "เทิง",
        "แม่ลาว",
        "แม่สรวย",
        "เวียงแก่น",
        "เวียงชัย",
        "เวียงป่าเป้า",
        "เขาสมิง",
        "คลองใหญ่",
        "บ่อไร่",
        "นาแก",
        "นาทม",
        "นาหว้า",
        "บ้านแพง",
        "ปลาปาก",
        "โพนสวรรค์",
        "เรณูนคร",
        "วังยาง",
        "ศรีสงคราม",
        "เฉลิมพระเกียรติ",
        "เมือง",
        "ปากคาด",
        "พรเจริญ",
        "ศรีวิไล",
        "ป้อมปราบศัตรูพ่าย",
        "พระนคร",
        "สามโคก",
        "บางสะพานน้อย",
        "บึงกุ่ม",
        "ภาษีเจริญ",
        "วังทองหลาง",
        "ห้วยขวาง",
        "หนอกจอก",
        "สะพานสูง",
    )

    tambons = (
        "บางแค",
        "บางแค",
        "บางไผ่",
        "บางปะกอก",
        "ยางตลาด",
        "ดอนสมบูรณ์",
        "หัวงัว",
        "นาเชือก",
        "เทพศิรินทร์",
        "อุ่มเม่า",
        "คลองขาม",
        "บัวบาน",
        "เขาพระนอน",
        "เว่อ",
        "นาดี",
        "อิตื้อ",
        "โนนสูง",
        "หัวนาคำ",
        "หนองตอกแป้น",
        "หนองอิเฒ่า",
        "โนนศิลา",
        "หนองปลาหมอ",
        "เปือยใหญ่",
        "โนนแดง",
        "ก้อนแก้ว",
        "คลองเขื่อน",
        "บางเล่า",
        "บางโรง",
        "บางตลาด",
        "เนินขาม",
        "กะบกเตี้ย",
        "สุขเดือนห้า",
        "พะโต๊ะ",
        "ปากทรง",
        "ปังหวาน",
        "พระรักษ์",
        "ห้วยยอด",
        "ปากคม",
        "หนองช้างแล่น",
        "ท่างิ้ว",
        "บางดี",
        "ลำภูรา",
        "บางกุ้ง",
        "นาวง",
        "เขากอบ",
        "เขาขาว",
        "ในเตา",
        "เขาปูน",
        "ทุ่งต่อ",
        "ปากแจ่ม",
        "เกาะหวาย",
        "ปากพลี",
        "เกาะโพธิ์",
        "ท่าเรือ",
        "โคกกรวด",
        "หนองแสง",
        "นาหินลาด",
    )

    tambon_prefixes = OrderedDict(
        (
            ("", 40.0),
            ("วัด", 2.0),
            ("บ้าน", 2.0),
            ("บ่อ", 2.0),
            ("บึง", 2.0),
            ("ป่า", 1.0),
            ("ห้วย", 1.0),
        )
    )

    tambon_suffixes = OrderedDict(
        (
            ("", 30),
            ("เหนือ", 3),
            ("ใต้", 3),
            ("ใหญ่", 2),
            ("กลาง", 1),
            ("เล็ก", 1),
            ("ใหม่", 1),
            ("เดิม", 0.1),
        )
    )

    city_suffixes = ("นคร",)

    def street_prefix(self) -> str:
        """
        :example: 'ถนน'
        """
        return self.random_element(self.street_prefixes)

    def administrative_unit(self) -> str:
        """
        :example: 'อุบลราชธานี'
        """
        return self.random_element(self.provinces)

    province = administrative_unit

    def amphoe(self) -> str:
        """
        Get a random Amphoe (district) name.
        Currently it's total random and not necessarily matched with a province.
        :example: 'บางสะพานน้อย'
        """
        return self.random_element(self.amphoes)

    def tambon(self) -> str:
        """
        Get a random Tambon (subdistrict) name.
        Currently it's total random and not necessarily matched with an amphoe or province.
        :example: 'ห้วยนาง'
        """
        return (
            f"{self.random_element(self.tambon_prefixes)}{self.random_element(self.tambons)}"
            + f"{self.random_element(self.tambon_suffixes)}"
        )

    def city_name(self) -> str:
        return self.random_element(self.cities)
