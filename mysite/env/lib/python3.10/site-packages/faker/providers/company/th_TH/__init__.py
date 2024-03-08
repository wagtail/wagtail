from collections import OrderedDict

from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = OrderedDict(
        (
            ("{{company_limited_prefix}}{{last_name}} {{company_limited_suffix}}", 0.2),
            (
                "{{company_limited_prefix}}{{last_name}}{{company_suffix}} {{company_limited_suffix}}",
                0.2,
            ),
            ("{{company_limited_prefix}}{{last_name}} {{company_limited_suffix}}", 0.2),
            ("{{company_prefix}}{{last_name}}", 0.2),
            ("{{company_prefix}}{{last_name}}{{company_suffix}}", 0.2),
            ("{{last_name}}{{company_suffix}}", 0.1),
            ("{{nonprofit_prefix}}{{last_name}}", 0.1),
            ("{{last_name}}-{{last_name}}", 0.05),
            ("{{last_name}}และ{{last_name}}", 0.05),
            ("{{company_limited_prefix}}{{last_name}}", 0.01),
        )
    )

    company_prefixes = OrderedDict(
        (
            ("ห้างหุ้นส่วนจำกัด ", 0.3),
            ("หจก.", 0.2),
            ("บจก.", 0.1),
            ("บมจ.", 0.1),
            ("ห้างหุ้นส่วนสามัญ ", 0.1),
            ("หสน.", 0.01),
        )
    )

    nonprofit_prefixes = OrderedDict(
        (
            ("สมาคม", 0.4),
            ("มูลนิธิ", 0.3),
            ("ชมรม", 0.2),
            ("สหภาพแรงงาน", 0.1),
        )
    )

    company_suffixes = (
        "และเพื่อน",
        "และบุตร",
        "แอนด์ซันส์",
        "กรุ๊ป",
        "การช่าง",
        "ก่อสร้าง",
        "บริการ",
        "เซอร์วิส",
        "กลการ",
        "ซัพพลาย",
        "คอมมิวนิเคชั่น",
        "พืชผล",
        "เอเยนซี",
        "เอ็นจิเนียริ่ง",
        "คอนสตรัคชั่น",
        "วิศวกรรม",
        "วิศวการ",
        "คอมพิวเตอร์",
        "พานิช",
        "ขนส่ง",
        "เฟอนิชชิ่ง",
        "เฟอร์นิเจอร์",
        "อุตสาหกรรม",
        "เอนเตอรไพรส์",
        "จิวเวลรี่",
        "อะไหล่ยนต์",
        "ภาพยนตร์",
        "ยานยนต์",
        "เทรดดิ้ง",
        "การค้า",
        "แลบ",
        "เคมิคอล",
        "อิมปอร์ตเอ็กซปอร์ต",
        "อินเตอร์เนชั่นแนล",
        "บรรจุภัณฑ์",
        "แพคกิ้ง",
        "มอเตอร์",
        "โอสถ",
        "การบัญชี",
        "สโตร์",
    )

    company_limited_prefixes = OrderedDict(
        (
            ("บริษัท ", 0.95),
            ("ธนาคาร", 0.03),
            ("บริษัทหลักทรัพย์ ", 0.005),
            ("กองทุนรวม", 0.005),
        )
    )

    company_limited_suffixes = OrderedDict(
        (
            ("จำกัด", 0.85),
            ("จำกัด (มหาชน)", 0.15),
        )
    )

    def company_prefix(self) -> str:
        """
        :example: 'ห้างหุ้นส่วนจำกัด'
        """
        return self.random_element(self.company_prefixes)

    def company_limited_prefix(self) -> str:
        """
        :example: 'บริษัท'
        """
        return self.random_element(self.company_limited_prefixes)

    def company_limited_suffix(self) -> str:
        """
        :example: 'จำกัด'
        """
        return self.random_element(self.company_limited_suffixes)

    def nonprofit_prefix(self) -> str:
        """
        :example: 'มูลนิธิ'
        """
        return self.random_element(self.nonprofit_prefixes)
