from datetime import datetime
from embedly import Embedly

from django.conf import settings

from .models import Embed


def get_embed(url, max_width=None):
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
