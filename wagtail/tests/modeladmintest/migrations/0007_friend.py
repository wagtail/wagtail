# Generated by Django 2.1.3 on 2018-12-18 12:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modeladmintest', '0006_contributor_person_visitor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Friend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=255)),
                ('address', models.CharField(max_length=255)),
            ],
        ),
    ]
