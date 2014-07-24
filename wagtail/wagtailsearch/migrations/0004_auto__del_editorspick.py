# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ('wagtaileditorspicks', '0001_initial'),
    )

    def forwards(self, orm):
        pass

    def backwards(self, orm):
        pass

    models = {
        'wagtailsearch.query': {
            'Meta': {'object_name': 'Query'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'query_string': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'wagtailsearch.querydailyhits': {
            'Meta': {'unique_together': "(('query', 'date'),)", 'object_name': 'QueryDailyHits'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'hits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'query': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'daily_hits'", 'to': "orm['wagtailsearch.Query']"})
        }
    }

    complete_apps = ['wagtailsearch']