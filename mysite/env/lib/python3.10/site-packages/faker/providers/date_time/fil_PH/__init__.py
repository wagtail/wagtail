from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    """Provider for datetimes for fil_PH locale"""

    DAY_NAMES = {
        "0": "Linggo",
        "1": "Lunes",
        "2": "Martes",
        "3": "Miyerkules",
        "4": "Huwebes",
        "5": "Biyernes",
        "6": "Sabado",
    }
    MONTH_NAMES = {
        "01": "Enero",
        "02": "Pebrero",
        "03": "Marso",
        "04": "Abril",
        "05": "Mayo",
        "06": "Hunyo",
        "07": "Hulyo",
        "08": "Agosto",
        "09": "Setyembre",
        "10": "Oktubre",
        "11": "Nobyembre",
        "12": "Disyembre",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
