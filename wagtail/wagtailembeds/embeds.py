from datetime import datetime


from django.conf import settings

from .models import Embed

import os
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'endpoints.json')
print file_path
print open(file_path).read()


def get_embed_embedly(url, max_width=None):
    # Check database
    try:
        return Embed.objects.get(url=url, max_width=max_width)
    except Embed.DoesNotExist:
        pass

    try:
        # Call embedly API
        client = Embedly(key=settings.EMBEDLY_KEY)
    except AttributeError:
        return None
    if max_width is not None:
        oembed = client.oembed(url, maxwidth=max_width, better=False)
    else:
        oembed = client.oembed(url, better=False)

    # Check for error
    if oembed.get('error'):
        return None

    # Save result to database
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

    # Return new embed
    return row

def get_embed_oembed(url, max_width=None):
    pass
    
get_embed = get_embed_oembed    
try:
    from embedly import Embedly
    if hasattr(settings,'EMBEDLY_KEY'):
        get_embed = get_embed_embedly
except:
    pass
        
print get_embed

        