from wagtail.admin.rich_text.converters.html_to_contentstate import HtmlToContentStateHandler


class ContentstateConverter():
    def __init__(self, features=None):
        self.features = features
        self.html_to_contentstate_handler = HtmlToContentStateHandler(features)

    def from_database_format(self, html):
        self.html_to_contentstate_handler.reset()
        self.html_to_contentstate_handler.feed(html)
        return self.html_to_contentstate_handler.contentstate.as_json(indent=4, separators=(',', ': '))
