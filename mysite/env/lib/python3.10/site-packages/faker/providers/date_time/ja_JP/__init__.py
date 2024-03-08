from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    MONTH_NAMES = {
        "01": "一月",
        "02": "二月",
        "03": "三月",
        "04": "四月",
        "05": "五月",
        "06": "六月",
        "07": "七月",
        "08": "八月",
        "09": "九月",
        "10": "十月",
        "11": "十一月",
        "12": "十二月",
    }

    TRADITIONAL_MONTH_NAMES = {
        "01": "睦月",
        "02": "如月",
        "03": "弥生",
        "04": "卯月",
        "05": "皐月",
        "06": "水無月",
        "07": "文月",
        "08": "葉月",
        "09": "長月",
        "10": "神無月",
        "11": "霜月",
        "12": "師走",
    }
    DAY_NAMES = {
        "0": "日曜日",
        "1": "月曜日",
        "2": "火曜日",
        "3": "水曜日",
        "4": "木曜日",
        "5": "金曜日",
        "6": "土曜日",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]

    def traditional_month_name(self) -> str:
        month = self.month()
        return self.TRADITIONAL_MONTH_NAMES[month]
