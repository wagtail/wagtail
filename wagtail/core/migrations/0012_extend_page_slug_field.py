# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0011_page_first_published_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='slug',
            field=models.SlugField(
                help_text='The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/',
                max_length=255
            ),
            preserve_default=True,
        ),
    ]
