from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "mandag",
        "1": "tirsdag",
        "2": "onsdag",
        "3": "torsdag",
        "4": "fredag",
        "5": "lørdag",
        "6": "søndag",
    }

    MONTH_NAMES = {
        "01": "januar",
        "02": "februar",
        "03": "marts",
        "04": "april",
        "05": "maj",
        "06": "juni",
        "07": "juli",
        "08": "august",
        "09": "september",
        "10": "oktober",
        "11": "november",
        "12": "decembder",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
