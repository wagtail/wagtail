from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "Nedelja",
        "1": "Ponedeljek",
        "2": "Torek",
        "3": "Sreda",
        "4": "Četrtek",
        "5": "Petek",
        "6": "Sobota",
    }

    MONTH_NAMES = {
        "01": "Januar",
        "02": "Februar",
        "03": "Marec",
        "04": "April",
        "05": "Maj",
        "06": "Junij",
        "07": "Julij",
        "08": "Avgust",
        "09": "September",
        "10": "Oktober",
        "11": "November",
        "12": "December",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]
