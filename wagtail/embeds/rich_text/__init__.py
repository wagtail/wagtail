from wagtail.embeds import format


# Front-end conversion

class MediaEmbedHandler:
    @staticmethod
    def expand_db_attributes(attrs):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use on the front-end.
        """
        return format.embed_to_frontend_html(attrs['url'])
