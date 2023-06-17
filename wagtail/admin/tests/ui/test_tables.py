from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.utils.html import format_html

from wagtail.admin.ui.tables import (
    BaseColumn,
    Column,
    RelatedObjectsColumn,
    Table,
    TitleColumn,
)
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

    def test_table_render_with_caption(self):
        data = [
            {"first_name": "Paul", "last_name": "Simon"},
            {"first_name": "Art", "last_name": "Garfunkel"},
        ]

        caption = "Test table"

        table = Table(
            columns=[
                Column("first_name"),
                Column("last_name"),
            ],
            data=data,
            caption=caption,
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            """
            <table class="listing">
                <caption class="w-sr-only">Test table</caption>
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
                    link_attrs={"data-chooser": "yes"},
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
                                <a href="/admin/sites/edit/%d/" class="choose-site" data-chooser="yes">blog.example.com</a>
                            </div>
                        </td>
                        <td>My blog</td>
                    </tr>
                    <tr>
                        <td class="title">
                            <div class="title-wrapper">
                                <a href="/admin/sites/edit/%d/" class="choose-site" data-chooser="yes">gallery.example.com</a>
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

    def test_row_classname(self):
        class SiteTable(Table):
            def get_row_classname(self, instance):
                return "default-site" if instance.is_default_site else ""

        root_page = Page.objects.filter(depth=2).first()
        blog = Site.objects.create(
            hostname="blog.example.com",
            site_name="My blog",
            root_page=root_page,
            is_default_site=True,
        )
        gallery = Site.objects.create(
            hostname="gallery.example.com", site_name="My gallery", root_page=root_page
        )
        data = [blog, gallery]

        table = SiteTable(
            [
                Column("hostname"),
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
                    <tr class="default-site">
                        <td>blog.example.com</td>
                        <td>My blog</td>
                    </tr>
                    <tr>
                        <td>gallery.example.com</td>
                        <td>My gallery</td>
                    </tr>
                </tbody>
            </table>
        """,
        )

    def test_row_attrs(self):
        class SiteTable(Table):
            def get_row_attrs(self, instance):
                attrs = super().get_row_attrs(instance)
                attrs["data-id"] = instance.pk
                return attrs

        root_page = Page.objects.filter(depth=2).first()
        blog = Site.objects.create(
            hostname="blog.example.com",
            site_name="My blog",
            root_page=root_page,
            is_default_site=True,
        )
        gallery = Site.objects.create(
            hostname="gallery.example.com", site_name="My gallery", root_page=root_page
        )
        data = [blog, gallery]

        table = SiteTable(
            [
                Column("hostname"),
                Column("site_name", label="Site name"),
            ],
            data,
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            f"""
            <table class="listing">
                <thead>
                    <tr><th>Hostname</th><th>Site name</th></tr>
                </thead>
                <tbody>
                    <tr data-id="{blog.pk}">
                        <td>blog.example.com</td>
                        <td>My blog</td>
                    </tr>
                    <tr data-id="{gallery.pk}">
                        <td>gallery.example.com</td>
                        <td>My gallery</td>
                    </tr>
                </tbody>
            </table>
        """,
        )

    def test_table_and_row_in_context(self):
        data = [
            {"first_name": "Paul", "last_name": "Simon"},
            {"first_name": "Art", "last_name": "Garfunkel"},
        ]

        class CounterColumn(BaseColumn):
            def render_cell_html(self, instance, parent_context):
                context = self.get_cell_context_data(instance, parent_context)
                return format_html(
                    "<td>{} of {}</td>",
                    context["row"].index + 1,
                    context["table"].row_count,
                )

        table = Table(
            [
                CounterColumn("index"),
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
                    <tr><th>Index</th><th>First name</th><th>Last name</th></tr>
                </thead>
                <tbody>
                    <tr><td>1 of 2</td><td>Paul</td><td>Simon</td></tr>
                    <tr><td>2 of 2</td><td>Art</td><td>Garfunkel</td></tr>
                </tbody>
            </table>
        """,
        )


class TestRelatedObjectsColumn(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def render_component(self, obj):
        request = self.rf.get("/")
        template = Template("{% load wagtailadmin_tags %}{% component obj %}")
        return template.render(Context({"request": request, "obj": obj}))

    def test_table_render(self):
        table = Table(
            [
                Column("title"),
                RelatedObjectsColumn("sites_rooted_here"),
            ],
            Page.objects.all(),
        )

        html = self.render_component(table)
        self.assertHTMLEqual(
            html,
            """
            <table class="listing">
                <thead>
                    <tr><th>Title</th><th>Sites rooted here</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Root</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>Welcome to your new Wagtail site!</td>
                        <td><ul><li>localhost [default]</li></ul></td>
                    </tr>
                </tbody>
            </table>
        """,
        )
