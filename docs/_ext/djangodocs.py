# taken from:
# http://reinout.vanrees.org/weblog/2012/12/01/django-intersphinx.html


def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
