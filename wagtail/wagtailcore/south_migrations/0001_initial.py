# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from wagtail.wagtailcore.compat import AUTH_USER_MODEL, AUTH_USER_MODEL_NAME


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Site'
        db.create_table(u'wagtailcore_site', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('port', self.gf('django.db.models.fields.IntegerField')(default=80)),
            ('root_page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sites_rooted_here', to=orm['wagtailcore.Page'])),
            ('is_default_site', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'wagtailcore', ['Site'])

        # Adding model 'Page'
        db.create_table(u'wagtailcore_page', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('depth', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('numchild', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pages', to=orm['contenttypes.ContentType'])),
            ('live', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('has_unpublished_changes', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('url_path', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='owned_pages', null=True, to=orm[AUTH_USER_MODEL])),
            ('seo_title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('show_in_menus', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('search_description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'wagtailcore', ['Page'])

        # Adding model 'PageRevision'
        db.create_table(u'wagtailcore_pagerevision', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['wagtailcore.Page'])),
            ('submitted_for_moderation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[AUTH_USER_MODEL], null=True, blank=True)),
            ('content_json', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'wagtailcore', ['PageRevision'])

        # Adding model 'GroupPagePermission'
        db.create_table(u'wagtailcore_grouppagepermission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='page_permissions', to=orm['auth.Group'])),
            ('page', self.gf('django.db.models.fields.related.ForeignKey')(related_name='group_permissions', to=orm['wagtailcore.Page'])),
            ('permission_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
        ))
        db.send_create_signal(u'wagtailcore', ['GroupPagePermission'])


    def backwards(self, orm):
        # Deleting model 'Site'
        db.delete_table(u'wagtailcore_site')

        # Deleting model 'Page'
        db.delete_table(u'wagtailcore_page')

        # Deleting model 'PageRevision'
        db.delete_table(u'wagtailcore_pagerevision')

        # Deleting model 'GroupPagePermission'
        db.delete_table(u'wagtailcore_grouppagepermission')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        AUTH_USER_MODEL: {
            'Meta': {'object_name': AUTH_USER_MODEL_NAME},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'wagtailcore.grouppagepermission': {
            'Meta': {'object_name': 'GroupPagePermission'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'page_permissions'", 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'group_permissions'", 'to': u"orm['wagtailcore.Page']"}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        u'wagtailcore.page': {
            'Meta': {'object_name': 'Page'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages'", 'to': u"orm['contenttypes.ContentType']"}),
            'depth': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'has_unpublished_changes': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'live': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'numchild': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_pages'", 'null': 'True', 'to': u"orm['%s']" % AUTH_USER_MODEL}),
            'path': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'search_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'seo_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'show_in_menus': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'wagtailcore.pagerevision': {
            'Meta': {'object_name': 'PageRevision'},
            'content_json': ('django.db.models.fields.TextField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': u"orm['wagtailcore.Page']"}),
            'submitted_for_moderation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['%s']" % AUTH_USER_MODEL, 'null': 'True', 'blank': 'True'})
        },
        u'wagtailcore.site': {
            'Meta': {'object_name': 'Site'},
            'hostname': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default_site': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': '80'}),
            'root_page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sites_rooted_here'", 'to': u"orm['wagtailcore.Page']"})
        }
    }

    complete_apps = ['wagtailcore']