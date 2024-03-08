from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    def day_of_week(self) -> str:
        day = self.date("%w")
        DAY_NAMES = {
            "0": "सोमवार",
            "1": "मंगलवार",
            "2": "बुधवार",
            "3": "गुरुवार",
            "4": "जुम्मा",
            "5": "शनिवार",
            "6": "रविवार",
        }

        return DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        MONTH_NAMES = {
            "01": "जनवरी",
            "02": "फ़रवरी",
            "03": "मार्च",
            "04": "अप्रैल",
            "05": "मई",
            "06": "जून",
            "07": "जुलाई",
            "08": "अगस्त",
            "09": "सितंबर",
            "10": "अक्टूबर",
            "11": "नवंबर",
            "12": "दिसंबर",
        }

        return MONTH_NAMES[month]
