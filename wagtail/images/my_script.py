from django_config import *
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")  
settings.configure()

from wagtail.images.formats import get_image_format
