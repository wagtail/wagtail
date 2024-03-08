from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "neděle",
        "1": "pondělí",
        "2": "úterý",
        "3": "středa",
        "4": "čtvrtek",
        "5": "pátek",
        "6": "sobota",
    }

    MONTH_NAMES = {
        "01": "leden",
        "02": "únor",
        "03": "březen",
        "04": "duben",
        "05": "květen",
        "06": "červen",
        "07": "červenec",
        "08": "srpen",
        "09": "září",
        "10": "říjen",
        "11": "listopad",
        "12": "prosinec",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
