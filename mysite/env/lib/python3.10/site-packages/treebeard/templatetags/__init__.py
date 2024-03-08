from django.template import Variable, VariableDoesNotExist


action_form_var = Variable('action_form')


def needs_checkboxes(context):
    try:
        return action_form_var.resolve(context) is not None
    except VariableDoesNotExist:
        return False
