from django.dispatch import Signal


init_new_page = Signal(providing_args=['page', 'parent'])
