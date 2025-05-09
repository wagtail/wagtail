from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("demosite", "0003_blogentrypagetag_fk_for_django_4"),
    ]

    operations = [
        migrations.AlterField(
            model_name='formfield',
            name='clean_name',
            field=models.CharField(
                blank=True,
                default='',
                verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
    ]
