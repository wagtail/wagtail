# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-16 17:15
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("wagtailimages", "0017_reduce_focal_point_key_max_length")]

    operations = [migrations.RemoveField(model_name="rendition", name="filter")]
