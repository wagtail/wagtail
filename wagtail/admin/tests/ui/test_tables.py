from wagtail.admin.ui.tables import Column, Table

from django.template import Context, Template
from django.test import RequestFactory, TestCase


class TestTable(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def render_component(self, obj):
        request = self.rf.get('/')
        template = Template("{% load wagtailadmin_tags %}{% component obj %}")
        return template.render(Context({'request': request, 'obj': obj}))

    def test_table_render(self):
        data = [
            {'first_name': 'Paul', 'last_name': 'Simon'},
            {'first_name': 'Art', 'last_name': 'Garfunkel'},
        ]

        table = Table([
            Column('first_name'),
            Column('last_name'),
        ], data)

        html = self.render_component(table)
        self.assertHTMLEqual(html, '''
            <table class="listing">
                <thead>
                    <tr><th>First name</th><th>Last name</th></tr>
                </thead>
                <tbody>
                    <tr><td>Paul</td><td>Simon</td></tr>
                    <tr><td>Art</td><td>Garfunkel</td></tr>
                </tbody>
            </table>
        ''')
