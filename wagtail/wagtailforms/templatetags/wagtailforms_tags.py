from django import template

register = template.Library()


@register.assignment_tag
def get_form_field(field, form):
    '''Finds the form field in form.fields that relates to the passed in field.'''
    return form[field.block.clean_name(field.value)]
