from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """
    Implement automotive provider for `zh_CN` locale.
    electric vehicles or downtown-restricted plates are not included
    """

    province_code = (
        "京",
        "津",
        "冀",
        "晋",
        "蒙",
        "辽",
        "吉",
        "黑",
        "沪",
        "苏",
        "浙",
        "皖",
        "闽",
        "赣",
        "鲁",
        "豫",
        "鄂",
        "湘",
        "粤",
        "桂",
        "琼",
        "渝",
        "川",
        "贵",
        "云",
        "藏",
        "陕",
        "甘",
        "青",
        "宁",
        "新",
    )

    def license_plate(self) -> str:
        """Generate a license plate."""
        pattern: str = str(self.random_element(self.province_code)) + self.random_uppercase_letter() + "-#####"
        return self.numerify(self.generator.parse(pattern))
