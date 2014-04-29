# encoding: utf8
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0002_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rendition',
            fields=[
                (u'id', models.AutoField(verbose_name=u'ID', serialize=False, auto_created=True, primary_key=True)),
                ('filter', models.ForeignKey(to='wagtailimages.Filter', to_field=u'id')),
                ('file', models.ImageField(height_field='height', width_field='width', upload_to='images')),
                ('width', models.IntegerField(editable=False)),
                ('height', models.IntegerField(editable=False)),
                ('image', models.ForeignKey(to='wagtailimages.Image', to_field=u'id')),
            ],
            options={
                u'unique_together': set([('image', 'filter')]),
            },
            bases=(models.Model,),
        ),
    ]
