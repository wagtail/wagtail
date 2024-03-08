from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "Bazar",
        "1": "Bazar ertəsi",
        "2": "Çərşənbə axşamı",
        "3": "Çərşənbə",
        "4": "Cümə axşamı",
        "5": "Cümə",
        "6": "Şənbə",
    }

    MONTH_NAMES = {
        "01": "Yanvar",
        "02": "Fevral",
        "03": "Mart",
        "04": "Aprel",
        "05": "May",
        "06": "İyun",
        "07": "İyul",
        "08": "Avqust",
        "09": "Sentyabr",
        "10": "Oktyabr",
        "11": "Noyabr",
        "12": "Dekabr",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
