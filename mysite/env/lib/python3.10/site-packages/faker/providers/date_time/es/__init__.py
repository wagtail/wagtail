from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "domingo",
        "1": "lunes",
        "2": "martes",
        "3": "miércoles",
        "4": "jueves",
        "5": "viernes",
        "6": "sábado",
    }

    MONTH_NAMES = {
        "01": "enero",
        "02": "febrero",
        "03": "marzo",
        "04": "abril",
        "05": "mayo",
        "06": "junio",
        "07": "julio",
        "08": "agosto",
        "09": "septiembre",
        "10": "octubre",
        "11": "noviembre",
        "12": "diciembre",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
