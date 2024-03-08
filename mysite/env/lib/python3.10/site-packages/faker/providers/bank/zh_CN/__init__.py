from .. import Provider as BankProvider


class Provider(BankProvider):
    """Implement bank provider for ``zh_CN`` locale.
    Source: https://zh.wikipedia.org/wiki/中国大陆银行列表
    """

    banks = (
        "中国人民银行",
        "国家开发银行",
        "中国进出口银行",
        "中国农业发展银行",
        "交通银行",
        "中国银行",
        "中国建设银行",
        "中国农业银行",
        "中国工商银行",
        "中国邮政储蓄银行",
        "中国光大银行",
        "中国民生银行",
        "招商银行",
        "中信银行",
        "华夏银行",
        "上海浦东发展银行",
        "平安银行",
        "广发银行",
        "兴业银行",
        "浙商银行",
        "渤海银行",
        "恒丰银行",
        "西安银行",
    )

    def bank(self) -> str:
        """Generate a bank name."""
        return self.random_element(self.banks)
