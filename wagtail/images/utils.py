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


def parse_color_string(color_string):
    """
    Parses a string a user typed into a tuple of 3 integers representing the
    red, green and blue channels respectively.

    May raise a ValueError if the string cannot be parsed.

    The colour string must be a CSS 3 or 6 digit hex code without the '#' prefix.
    """
    if len(color_string) == 3:
        r = int(color_string[0], 16) * 17
        g = int(color_string[1], 16) * 17
        b = int(color_string[2], 16) * 17
    elif len(color_string) == 6:
        r = int(color_string[0:2], 16)
        g = int(color_string[2:4], 16)
        b = int(color_string[4:6], 16)
    else:
        ValueError('Color string must be either 3 or 6 hexadecimal digits long')

    return r, g, b
