from django.utils.safestring import mark_safe

from wagtail.core import hooks


@hooks.register('register_icons')
def register_icons(icons):
    icons.append('customapp/rocket.svg')
    return icons


class WelcomePanel:
    order = 100

    def render(self):
        return mark_safe("""
        <section class="panel summary nice-padding">
        
            <p>
                <-- Images, Documents, Snippets and Forms icons are converted form Wagtail Font => SVG's. 
                The other menu items are replaced by js (?)
            </p>
            <p>
                The icons in the pages drawer (React) are also SVG's. But no styling (yet).
            </p>
        
            <p>
                <-- Documents icon is customised by template override. 
                See `wagtail/customapp/templates/wagtailadmin/icons/symbols/doc-full-inverse.svg`
            </p>

            <svg class="svg-icon" aria-hidden="true">
                <use href="#foo-rocket"></use>
            </svg>
            <p>
                ^-- This rocket lives in the wagtail.customapp. It is hooked via `customapp/wagtail_hooks.py`.
            </p>

        </section>
        """)


@hooks.register('construct_homepage_panels')
def add_another_welcome_panel(request, panels):
    return panels.append(WelcomePanel())
