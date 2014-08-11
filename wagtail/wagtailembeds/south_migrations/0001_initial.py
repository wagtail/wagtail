# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("wagtailcore", "0002_initial_data"),
    )

    def forwards(self, orm):
        # Adding model 'Embed'
        db.create_table('wagtailembeds_embed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('max_width', self.gf('django.db.models.fields.SmallIntegerField')
             (null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('html', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('thumbnail_url', self.gf('django.db.models.fields.URLField')
             (max_length=200, null=True, blank=True)),
            ('width', self.gf('django.db.models.fields.IntegerField')
             (null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.IntegerField')
             (null=True, blank=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')
             (auto_now=True, blank=True)),
        ))
        db.send_create_signal('wagtailembeds', ['Embed'])

        # Adding unique constraint on 'Embed', fields ['url', 'max_width']
        db.create_unique('wagtailembeds_embed', ['url', 'max_width'])

    def backwards(self, orm):
        # Removing unique constraint on 'Embed', fields ['url', 'max_width']
        db.delete_unique('wagtailembeds_embed', ['url', 'max_width'])

        # Deleting model 'Embed'
        db.delete_table('wagtailembeds_embed')

    models = {
        'wagtailembeds.embed': {
            'Meta': {'unique_together': "(('url', 'max_width'),)", 'object_name': 'Embed'},
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'max_width': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'thumbnail_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['wagtailembeds']
