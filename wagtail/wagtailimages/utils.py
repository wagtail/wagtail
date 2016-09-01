from __future__ import absolute_import, unicode_literals


# Helper functions for migrating the Rendition.filter foreign key to the filter_spec field,
# and the corresponding reverse migration

def get_fill_filter_spec_migrations(app_name, rendition_model_name):

    def fill_filter_spec_forward(apps, schema_editor):
        # Populate Rendition.filter_spec with the spec string of the corresponding Filter object
        Rendition = apps.get_model(app_name, rendition_model_name)
        Filter = apps.get_model('wagtailimages', 'Filter')

        db_alias = schema_editor.connection.alias
        for flt in Filter.objects.using(db_alias):
            renditions = Rendition.objects.using(db_alias).filter(filter=flt, filter_spec='')
            renditions.update(filter_spec=flt.spec)

    def fill_filter_spec_reverse(apps, schema_editor):
        # Populate the Rendition.filter
        Rendition = apps.get_model(app_name, rendition_model_name)
        Filter = apps.get_model('wagtailimages', 'Filter')
        db_alias = schema_editor.connection.alias

        filters_by_spec = {}
        for rendition in Rendition.objects.using(db_alias):
            try:
                filter = filters_by_spec[rendition.filter_spec]
            except KeyError:
                filter, _ = Filter.objects.get_or_create(spec=rendition.filter_spec)
                filters_by_spec[rendition.filter_spec] = filter

            rendition.filter = filter
            rendition.save()

    return (fill_filter_spec_forward, fill_filter_spec_reverse)
