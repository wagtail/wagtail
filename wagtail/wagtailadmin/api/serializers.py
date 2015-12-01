from wagtail.api.v2.serializers import PageMetaField, PageSerializer


class AdminPageMetaField(PageMetaField):
    """
    A subclass of PageMetaField for the admin API.

    This adds the "status" field to the representation

    Example:

    "meta": {
        ...

        "status": "live"
    }
    """
    def to_representation(self, page):
        data = super(AdminPageMetaField, self).to_representation(page)
        data['status'] = page.status_string
        data['has_children'] = page.numchild > 0
        return data


class AdminPageSerializer(PageSerializer):
    meta = AdminPageMetaField()
