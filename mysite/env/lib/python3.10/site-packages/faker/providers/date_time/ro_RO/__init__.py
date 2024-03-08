from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "duminica",
        "1": "luni",
        "2": "marti",
        "3": "miercuri",
        "4": "joi",
        "5": "vineri",
        "6": "sambata",
    }

    MONTH_NAMES = {
        "01": "ianuarie",
        "02": "februarie",
        "03": "martie",
        "04": "aprilie",
        "05": "mai",
        "06": "iunie",
        "07": "iulie",
        "08": "august",
        "09": "septembrie",
        "10": "octombrie",
        "11": "noiembrie",
        "12": "decembrie",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
