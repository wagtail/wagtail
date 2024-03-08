from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "dimanche",
        "1": "lundi",
        "2": "mardi",
        "3": "mercredi",
        "4": "jeudi",
        "5": "vendredi",
        "6": "samedi",
    }
    MONTH_NAMES = {
        "01": "Janvier",
        "02": "Février",
        "03": "Mars",
        "04": "Avril",
        "05": "Mai",
        "06": "Juin",
        "07": "Juillet",
        "08": "Août",
        "09": "Septembre",
        "10": "Octobre",
        "11": "Novembre",
        "12": "Décembre",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]
