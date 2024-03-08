from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    # Source: http://www.localeplanet.com/icu/ta-IN/index.html
    DAY_NAMES = {
        "0": "திங்கள்",
        "1": "செவ்வாய்",
        "2": "புதன்",
        "3": "வியாழன்",
        "4": "வெள்ளி",
        "5": "சனி",
        "6": "ஞாயிறு",
    }

    MONTH_NAMES = {
        "01": "ஜனவரி",
        "02": "பிப்ரவரி",
        "03": "மார்ச்",
        "04": "ஏப்ரல்",
        "05": "மே",
        "06": "ஜூன்",
        "07": "ஜூலை",
        "08": "ஆகஸ்ட்",
        "09": "செப்டம்பர்",
        "10": "அக்டோபர்",
        "11": "நவம்பர்",
        "12": "டிசம்பர்",
    }

    def day_of_week(self) -> str:
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self) -> str:
        month = self.month()
        return self.MONTH_NAMES[month]
