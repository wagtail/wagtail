from .. import Provider as DateTimeProvider


class Provider(DateTimeProvider):
    DAY_NAMES = {
        "0": "Κυριακή",
        "1": "Δευτέρα",
        "2": "Τρίτη",
        "3": "Τετάρτη",
        "4": "Πέμπτη",
        "5": "Παρασκευή",
        "6": "Σάββατο",
    }

    MONTH_NAMES = {
        "01": "Ιανουάριος",
        "02": "Φεβρουάριος",
        "03": "Μάρτιος",
        "04": "Απρίλιος",
        "05": "Μάιος",
        "06": "Ιούνιος",
        "07": "Ιούλιος",
        "08": "Αύγουστος",
        "09": "Σεπτέμβριος",
        "10": "Οκτώβριος",
        "11": "Νοέμβριος",
        "12": "Δεκέμβριος",
    }

    def day_of_week(self):
        day = self.date("%w")
        return self.DAY_NAMES[day]

    def month_name(self):
        month = self.month()
        return self.MONTH_NAMES[month]
