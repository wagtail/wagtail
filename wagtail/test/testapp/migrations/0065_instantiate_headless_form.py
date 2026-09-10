from django.db import migrations

# Test that frozen form page models can be instantiated without error -
# see https://github.com/wagtail/wagtail/issues/11911

def instantiate_form_page(apps, _):
    HeadlessForm = apps.get_model("tests", "HeadlessForm")
    HeadlessForm()


class Migration(migrations.Migration):
    dependencies = [
        ('tests', '0064_headlessform'),
    ]

    operations = [
        migrations.RunPython(instantiate_form_page, migrations.RunPython.noop),
    ]
