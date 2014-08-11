# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models, connection
from django.db.transaction import set_autocommit

class Migration(DataMigration):

    depends_on = (
        ("wagtailcore", "0002_initial_data"),
    )

    def forwards(self, orm):
        if connection.vendor == 'sqlite':
            set_autocommit(True)

        # Add a fake content type to hang the 'can access Wagtail admin' permission off.
        # The fact that this doesn't correspond to an actual defined model shouldn't matter, I hope...
        wagtailadmin_content_type = orm['contenttypes.ContentType'].objects.create(
            app_label='wagtailadmin', model='admin', name='Wagtail admin')
        admin_permission = orm['auth.permission'].objects.create(
            content_type=wagtailadmin_content_type, codename='access_admin', name='Can access Wagtail admin')

        for group in orm['auth.group'].objects.filter(name__in=['Editors', 'Moderators']):
            group.permissions.add(admin_permission)

    def backwards(self, orm):
        wagtailadmin_content_type = orm['contenttypes.ContentType'].objects.get(
            app_label='wagtailadmin', model='admin')
        orm['auth.Permission'].objects.filter(content_type=wagtailadmin_content_type).delete()
        wagtailadmin_content_type.delete()

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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
    }

    complete_apps = ['wagtailadmin']
    symmetrical = True
