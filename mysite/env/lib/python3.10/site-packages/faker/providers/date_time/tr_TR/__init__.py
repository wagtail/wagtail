from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "Pazar",
        "1": "Pazartesi",
        "2": "Salı",
        "3": "Çarşamba",
        "4": "Perşembe",
        "5": "Cuma",
        "6": "Cumartesi",
    }

    MONTH_NAMES = {
        "01": "Ocak",
        "02": "Şubat",
        "03": "Mart",
        "04": "Nisan",
        "05": "Mayıs",
        "06": "Haziran",
        "07": "Temmuz",
        "08": "Ağustos",
        "09": "Eylül",
        "10": "Ekim",
        "11": "Kasım",
        "12": "Aralık",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
