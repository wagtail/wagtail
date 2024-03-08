from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "zondag",
        "1": "maandag",
        "2": "dinsdag",
        "3": "woensdag",
        "4": "donderdag",
        "5": "vrijdag",
        "6": "zaterdag",
    }

    MONTH_NAMES = {
        "01": "januari",
        "02": "februari",
        "03": "maart",
        "04": "april",
        "05": "mei",
        "06": "juni",
        "07": "juli",
        "08": "augustus",
        "09": "september",
        "10": "oktober",
        "11": "november",
        "12": "december",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
