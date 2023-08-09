# Adding non-ModelAdmin views to a `ModelAdminGroup`

To add menu items to a `ModelAdminGroup` that are not managed by ModelAdmin, you can override the `get_submenu_items` method. For example, to add the calendar view described in [](../../../../extending/admin_views) alongside an `EventAdmin` modeladmin, you would do the following (in place of registering it through the `register_admin_menu_item` hook):

```{code-block} python
from django.urls import reverse
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    modeladmin_register,
    ModelAdminGroup,
)
from wagtail.admin.menu import MenuItem


class EventAdmin(ModelAdmin):
    model = CalendarEvent
    menu_label = "Events"
    menu_icon = "date"
    menu_order = 200
    list_display = ('title', 'date')


class CalendarGroup(ModelAdminGroup):
    menu_label = "Calendar events"
    menu_icon = "folder-open-inverse"
    menu_order = 900
    items = (EventAdmin,)

    def get_submenu_items(self):
        menu_items = super().get_submenu_items()
        menu_items.append(
            MenuItem('Calendar', reverse('calendar'), icon_name='date'),
        )
        return menu_items

modeladmin_register(CalendarGroup)
```
