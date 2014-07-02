from django.dispatch import Signal


page_published = Signal(providing_args=['instance'])
