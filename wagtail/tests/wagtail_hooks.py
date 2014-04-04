from wagtail.wagtailadmin import hooks

def editor_css():
    return """<link rel="stylesheet" href="/path/to/my/custom.css">"""
hooks.register('insert_editor_css', editor_css)


def editor_js():
    return """<script src="/path/to/my/custom.js"></script>"""
hooks.register('insert_editor_js', editor_js)
