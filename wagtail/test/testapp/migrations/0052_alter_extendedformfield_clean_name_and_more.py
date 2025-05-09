from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tests", "0051_userapprovaltaskstate_userapprovaltask"), 
    ]

    operations = [
        migrations.AlterField(
            model_name='extendedformfield',
            name='clean_name',
            field=models.CharField(
                 blank=True, default='', verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
        migrations.AlterField(
            model_name='formfieldforcustomlistviewpage',
            name='clean_name',
            field=models.CharField(
                 blank=True, default='', verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
        migrations.AlterField(
            model_name='formfieldwithcustomsubmission',
            name='clean_name',
            field=models.CharField(
                 blank=True, default='', verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
        migrations.AlterField(
            model_name='jadeformfield',
            name='clean_name',
            field=models.CharField(
                 blank=True, default='', verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
        migrations.AlterField(
            model_name='redirectformfield',
            name='clean_name',
            field=models.CharField(
                 blank=True, default='', verbose_name='name',
                help_text='Safe name of the form field, the label converted to ascii_snake_case',
            ),
        ),
    ]

