from datetime import datetime
from django.conf import settings
from ..models import Embed
import oembed_api

class EmbedlyException(Exception): pass
class AccessDeniedEmbedlyException(Exception): pass
class NotFoundEmbedlyException(Exception): pass

def get_embed_embedly(url, max_width=None):
    # Check database
    try:
        return Embed.objects.get(url=url, max_width=max_width)
    except Embed.DoesNotExist:
        pass

    client = Embedly(key=settings.EMBEDLY_KEY)
    
    if max_width is not None:
        oembed = client.oembed(url, maxwidth=max_width, better=False)
    else:
        oembed = client.oembed(url, better=False)

    # Check for error
    if oembed.get('error'):
        if oembed['error_code'] in [401,403]:
            raise AccessDeniedEmbedlyException
        elif oembed['error_code'] == 404:
            raise NotFoundEmbedlyException
        else:
            raise EmbedlyException

    return save_embed(url, max_width, oembed)
    

def get_embed_oembed(url, max_width=None):
    # Check database
    try:
        return Embed.objects.get(url=url, max_width=max_width)
    except Embed.DoesNotExist:
        pass

    oembed = oembed_api.get_embed_oembed(url, max_width)
    return save_embed(url, max_width, oembed)
    
   
def save_embed(url, max_width, oembed):
    row, created = Embed.objects.get_or_create(
        url=url,
        max_width=max_width,
        defaults={
            'type': oembed['type'],
            'title': oembed['title'],
            'thumbnail_url': oembed.get('thumbnail_url'),
            'width': oembed.get('width'),
            'height': oembed.get('height')
        }
    )

    if oembed['type'] == 'photo':
        html = '<img src="%s" />' % (oembed['url'], )
    else:
        html = oembed.get('html')

    if html:
        row.html = html
        row.last_updated = datetime.now()
        row.save()

    return row

# As a default use oembed
get_embed = get_embed_oembed    
try:
    from embedly import Embedly
    # if EMBEDLY_KEY is set and embedly library found the use embedly
    if hasattr(settings,'EMBEDLY_KEY'):
        get_embed = get_embed_embedly
except:
    pass
