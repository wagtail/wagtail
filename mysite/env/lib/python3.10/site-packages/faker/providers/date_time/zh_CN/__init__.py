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
    DAY_NAMES = {
        "0": "星期日",
        "1": "星期一",
        "2": "星期二",
        "3": "星期三",
        "4": "星期四",
        "5": "星期五",
        "6": "星期六",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]
