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
        # Populate the Rendition.filter field with Filter objects that match the spec in the
        # Rendition's filter_spec field
        Rendition = apps.get_model(app_name, rendition_model_name)
        Filter = apps.get_model('wagtailimages', 'Filter')
        db_alias = schema_editor.connection.alias

        while True:
            # repeat this process until we've confirmed that no remaining renditions exist with
            # a null 'filter' field - this minimises the possibility of new ones being inserted
            # by active server processes while the query is in progress

            # Find all distinct filter_spec strings used by renditions with a null 'filter' field
            unmatched_filter_specs = Rendition.objects.using(db_alias).filter(
                filter__isnull=True).values_list('filter_spec', flat=True).distinct()
            if not unmatched_filter_specs:
                break

            for filter_spec in unmatched_filter_specs:
                filter, _ = Filter.objects.using(db_alias).get_or_create(spec=filter_spec)
                Rendition.objects.using(db_alias).filter(filter_spec=filter_spec).update(filter=filter)

    return (fill_filter_spec_forward, fill_filter_spec_reverse)
