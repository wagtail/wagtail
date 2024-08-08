from wagtail.admin.widgets import Button


# This used to extend ListingButton – but since the universal listings design,
# all default buttons are now rendered inside a dropdown. Users listing never had
# separate hooks for top-level buttons and dropdown buttons (as they have no
# "more" button like pages have). As a result, we now extend Button so it doesn't
# have the default CSS classes that ListingButton adds. The class name is not
# changed to avoid unnecessary breaking changes.
class UserListingButton(Button):
    pass
