from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    MONTH_NAMES = {
        "01": "januar",
        "02": "februar",
        "03": "mars",
        "04": "april",
        "05": "mai",
        "06": "juni",
        "07": "juli",
        "08": "august",
        "09": "september",
        "10": "oktober",
        "11": "november",
        "12": "desember",
    }
    DAY_NAMES = {
        "0": "søndag",
        "1": "mandag",
        "2": "tirsdag",
        "3": "onsdag",
        "4": "torsdag",
        "5": "fredag",
        "6": "lørdag",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]
