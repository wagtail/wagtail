from django import forms

from wagtail.admin.staticfiles import versioned_static


class FilteredSelect(forms.Select):
    """
    A select box variant that adds 'data-' attributes to the <select> and <option> elements
    to allow the options to be dynamically filtered by another select box.
    See wagtailadmin/js/filtered-select.js for an example of how these attributes are configured.
    """

    def __init__(self, attrs=None, choices=(), filter_field=''):
        super().__init__(attrs, choices)
        self.filter_field = filter_field

    def build_attrs(self, base_attrs, extra_attrs=None):
        my_attrs = {
            'data-widget': 'filtered-select',
            'data-filter-field': self.filter_field,
        }
        if extra_attrs:
            my_attrs.update(extra_attrs)

        return super().build_attrs(base_attrs, my_attrs)

    def optgroups(self, name, value, attrs=None):
        # copy of Django's Select.optgroups, modified to accept filter_value as a
        # third item in the tuple and expose that as a data-filter-value attribute
        # on the final <option>
        groups = []
        has_selected = False

        for index, choice in enumerate(self.choices):
            try:
                (option_value, option_label, filter_value) = choice
            except ValueError:
                # *ChoiceField will still output blank options as a 2-tuple,
                # so need to handle that too
                (option_value, option_label) = choice
                filter_value = None

            if option_value is None:
                option_value = ''

            subgroup = []
            if isinstance(option_label, (list, tuple)):
                group_name = option_value
                subindex = 0
                choices = option_label
            else:
                group_name = None
                subindex = None
                choices = [(option_value, option_label)]
            groups.append((group_name, subgroup, index))

            for subvalue, sublabel in choices:
                selected = (
                    str(subvalue) in value
                    and (not has_selected or self.allow_multiple_selected)
                )
                has_selected |= selected

                subgroup.append(self.create_option(
                    name, subvalue, sublabel, selected, index, subindex=subindex,
                    filter_value=filter_value
                ))
                if subindex is not None:
                    subindex += 1
        return groups

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None, filter_value=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        if filter_value is not None:
            option['attrs']['data-filter-value'] = filter_value

        return option

    @property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/filtered-select.js'),
        ])
