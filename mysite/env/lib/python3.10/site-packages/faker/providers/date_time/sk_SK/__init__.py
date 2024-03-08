from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "nedeľa",
        "1": "pondelok",
        "2": "utorok",
        "3": "streda",
        "4": "štvrtok",
        "5": "piatok",
        "6": "sobota",
    }

    MONTH_NAMES = {
        "01": "január",
        "02": "február",
        "03": "marec",
        "04": "apríl",
        "05": "máj",
        "06": "jún",
        "07": "júl",
        "08": "august",
        "09": "september",
        "10": "október",
        "11": "november",
        "12": "december",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
