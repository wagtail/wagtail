from django.forms import widgets


class SwitchInput(widgets.CheckboxInput):
    template_name = 'wagtailadmin/widgets/switch.html'
