from __future__ import unicode_literals

from django.forms.utils import flatatt
from django.template import TemplateSyntaxError
from django.template.loader import render_to_string

from .config import NAMESPACE
from .utils import WuiNode


class Button(WuiNode):
    """
    Usage::

        {% wuibutton kind="primary" element="button" name="submit" icon="cog" %}
            Press me
        {% endwuibutton %}

    All arguments are optional.

    ``element``:
    - What kind of button to render. Possible values are "a", "button", and
      "span", for `<a>`, `<button>`, and `<span>`
      respectively. Defaults to "a".

    ``kind``:
    - The kind of button to render - currently 'primary' or 'secondary' - defaults to  'primary'

    ``icon``:
    - Used to add an icon to the button. See the wagtailstyleguide for all
      the possible icons. Defaults to no icon

    ``icon_only``:
    - Visually removes text by applying the text-replace class

    ``icon_bicolor``:
    - Adds the bicolor aesthetic

    ``name``:
    - The name attribute for the button. Only applicable for "button" and
      "submit" button types. Defaults to no name.

    ``small``:
    - Makes the button small

    ``disabled``:
    - Makes the button take on the disabled appearance

    ``scheme``:
    - Makes the button take on the scheme supplied - currently only 'yes' and 'no' but it's not whitelisted so new ones can be passed through

    """

    TAG_NAME = NAMESPACE + 'button'

    elements = {
        'a': 'wagtailadmin/ui/button/a.html',
        'span': 'wagtailadmin/ui/button/span.html',
        'button': 'wagtailadmin/ui/button/button.html'
    }

    def render_template(self, context, element='a', kind='primary', icon=None, icon_only=False,
                        icon_bicolor=False, small=False, disabled=False, scheme=None, **attrs):
        classes = []
        if icon:
            classes.extend([
                'icon',
                'icon-' + icon
            ])

        if icon_only:
            classes.append('text-replace')

        if icon_bicolor:
            classes.append('bicolor')

        if scheme:
            classes.append(scheme)

        button_element = element
        if button_element not in self.elements:
            raise TemplateSyntaxError("'%s' unknown button type %s" % (
                self.TAG_NAME, button_element))

        if kind == 'secondary':
            classes.append('button-secondary')

        if small:
            classes.append('button-small')

        if disabled:
            classes.append('disabled')

        template = self.elements[button_element]

        return render_to_string(template, {
            'inner_html': self.inner.render(context),
            'classes': ' '.join(classes),
            'attrs': flatatt(attrs),
        })
