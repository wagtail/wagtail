from django.template.base import Library
from .button import Button

register = Library()

register.tag(Button.TAG_NAME, Button.handle)
