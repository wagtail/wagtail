from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "domenica",
        "1": "lunedì",
        "2": "martedì",
        "3": "mercoledì",
        "4": "giovedì",
        "5": "venerdì",
        "6": "sabato",
    }

    MONTH_NAMES = {
        "01": "gennaio",
        "02": "febbraio",
        "03": "marzo",
        "04": "aprile",
        "05": "maggio",
        "06": "giugno",
        "07": "luglio",
        "08": "agosto",
        "09": "settembre",
        "10": "ottobre",
        "11": "novembre",
        "12": "dicembre",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
