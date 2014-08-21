# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from wagtail.wagtailcore.compat import AUTH_USER_MODEL, AUTH_USER_MODEL_NAME


class Migration(SchemaMigration):

    depends_on = (
        ("wagtailcore", "0002_initial_data"),
    )

    def forwards(self, orm):
        # Adding model 'Query'
        db.create_table('wagtailsearch_query', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query_string', self.gf('django.db.models.fields.CharField')
             (unique=True, max_length=255)),
        ))
        db.send_create_signal('wagtailsearch', ['Query'])

        # Adding model 'QueryDailyHits'
        db.create_table('wagtailsearch_querydailyhits', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='daily_hits', to=orm['wagtailsearch.Query'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('hits', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('wagtailsearch', ['QueryDailyHits'])

        # Adding unique constraint on 'QueryDailyHits', fields ['query',
        # 'date']
        db.create_unique('wagtailsearch_querydailyhits', ['query_id', 'date'])

        # Adding model 'EditorsPick'
        db.create_table('wagtailsearch_editorspick', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('query', self.gf('django.db.models.fields.related.ForeignKey')
             (related_name='editors_picks', to=orm['wagtailsearch.Query'])),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')
             (to=orm['wagtailcore.Page'])),
            ('sort_order', self.gf('django.db.models.fields.IntegerField')
             (null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('wagtailsearch', ['EditorsPick'])

        # Adding model 'SearchTest'
        db.create_table('wagtailsearch_searchtest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('wagtailsearch', ['SearchTest'])

        # Adding model 'SearchTestChild'
        db.create_table('wagtailsearch_searchtestchild', (
            ('searchtest_ptr', self.gf('django.db.models.fields.related.OneToOneField')
             (to=orm[
                 'wagtailsearch.SearchTest'], unique=True, primary_key=True)),
            ('extra_content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('wagtailsearch', ['SearchTestChild'])

    def backwards(self, orm):
        # Removing unique constraint on 'QueryDailyHits', fields ['query',
        # 'date']
        db.delete_unique('wagtailsearch_querydailyhits', ['query_id', 'date'])

        # Deleting model 'Query'
        db.delete_table('wagtailsearch_query')

        # Deleting model 'QueryDailyHits'
        db.delete_table('wagtailsearch_querydailyhits')

        # Deleting model 'EditorsPick'
        db.delete_table('wagtailsearch_editorspick')

        # Deleting model 'SearchTest'
        db.delete_table('wagtailsearch_searchtest')

        # Deleting model 'SearchTestChild'
        db.delete_table('wagtailsearch_searchtestchild')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        AUTH_USER_MODEL: {
            'Meta': {'object_name': AUTH_USER_MODEL_NAME},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'user_set'", 'blank': 'True', 'to': "orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wagtailcore.page': {
            'Meta': {'object_name': 'Page'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': "orm['contenttypes.ContentType']"}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'has_unpublished_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'live': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_pages'", 'null': 'True', 'to': "orm['%s']" % AUTH_USER_MODEL}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'search_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'seo_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'show_in_menus': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'wagtailsearch.editorspick': {
            'Meta': {'ordering': "('sort_order',)", 'object_name': 'EditorsPick'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wagtailcore.Page']"}),
            'query': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'editors_picks'", 'to': "orm['wagtailsearch.Query']"}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
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
        },
        'wagtailsearch.searchtest': {
            'Meta': {'object_name': 'SearchTest'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'wagtailsearch.searchtestchild': {
            'Meta': {'object_name': 'SearchTestChild', '_ormbases': ['wagtailsearch.SearchTest']},
            'extra_content': ('django.db.models.fields.TextField', [], {}),
            'searchtest_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['wagtailsearch.SearchTest']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['wagtailsearch']
