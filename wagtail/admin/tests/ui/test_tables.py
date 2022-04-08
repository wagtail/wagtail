from django.template import Context, Template
from django.test import RequestFactory, TestCase

from wagtail.admin.ui.tables import Column, Table, TitleColumn
from wagtail.models import Page, Site


class TestTable(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.rf = RequestFactory()

    def render_component(self, obj):
        request = self.rf.get("/")
        template = Template("{% load wagtailadmin_tags %}{% component obj %}")
        return template.render(Context({"request": request, "obj": obj}))

    def test_table_render(self):
        data = [
            {"first_name": "Paul", "last_name": "Simon"},
            {"first_name": "Art", "last_name": "Garfunkel"},
        ]

        table = Table(
            [
                Column("first_name"),
                Column("last_name"),
            ],
            data,
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            """
            <table class="listing">
                <thead>
                    <tr><th>First name</th><th>Last name</th></tr>
                </thead>
                <tbody>
                    <tr><td>Paul</td><td>Simon</td></tr>
                    <tr><td>Art</td><td>Garfunkel</td></tr>
                </tbody>
            </table>
        """,
        )

    def test_table_render_with_width(self):
        data = [
            {"first_name": "Paul", "last_name": "Simon"},
            {"first_name": "Art", "last_name": "Garfunkel"},
        ]

        table = Table(
            [
                Column("first_name"),
                Column("last_name", width="75%"),
            ],
            data,
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            """
            <table class="listing">
                <col />
                <col width="75%" />
                <thead>
                    <tr><th>First name</th><th>Last name</th></tr>
                </thead>
                <tbody>
                    <tr><td>Paul</td><td>Simon</td></tr>
                    <tr><td>Art</td><td>Garfunkel</td></tr>
                </tbody>
            </table>
        """,
        )

    def test_title_column(self):
        root_page = Page.objects.filter(depth=2).first()
        blog = Site.objects.create(
            hostname="blog.example.com", site_name="My blog", root_page=root_page
        )
        gallery = Site.objects.create(
            hostname="gallery.example.com", site_name="My gallery", root_page=root_page
        )
        data = [blog, gallery]

        table = Table(
            [
                TitleColumn(
                    "hostname",
                    url_name="wagtailsites:edit",
                    link_classname="choose-site",
                ),
                Column("site_name", label="Site name"),
            ],
            data,
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            """
            <table class="listing">
                <thead>
                    <tr><th>Hostname</th><th>Site name</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="title">
                            <div class="title-wrapper">
                                <a href="/admin/sites/%d/" class="choose-site">blog.example.com</a>
                            </div>
                        </td>
                        <td>My blog</td>
                    </tr>
                    <tr>
                        <td class="title">
                            <div class="title-wrapper">
                                <a href="/admin/sites/%d/" class="choose-site">gallery.example.com</a>
                            </div>
                        </td>
                        <td>My gallery</td>
                    </tr>
                </tbody>
            </table>
        """
            % (blog.pk, gallery.pk),
        )

    def test_column_media(self):
        class FancyColumn(Column):
            class Media:
                js = ["js/gradient-fill.js"]

        data = [
            {"first_name": "Paul", "last_name": "Simon"},
            {"first_name": "Art", "last_name": "Garfunkel"},
        ]

        table = Table(
            [
                FancyColumn("first_name"),
                Column("last_name"),
            ],
            data,
        )

        self.assertIn('src="/static/js/gradient-fill.js"', str(table.media["js"]))
