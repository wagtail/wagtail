from django.utils.functional import SimpleLazyObject


def disallow_separator():
    raise ValueError("Separator used!")


THOUSAND_SEPARATOR = SimpleLazyObject(disallow_separator)
NUMBER_GROUPING = (1,)
