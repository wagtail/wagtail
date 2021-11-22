from wagtail.core.log_actions import log


class DeletePageAction:
    def __init__(self, page):
        self.page = page

    @staticmethod
    def log_deletion(page, user):
        log(
            instance=page,
            action="wagtail.delete",
            user=user,
            deleted=True,
        )

    def _delete_page(self, page, *args, **kwargs):
        from wagtail.core.models import Page

        # Ensure that deletion always happens on an instance of Page, not a specific subclass. This
        # works around a bug in treebeard <= 3.0 where calling SpecificPage.delete() fails to delete
        # child pages that are not instances of SpecificPage
        if type(page) is Page:
            user = kwargs.pop("user", None)

            if page.get_children().exists():
                for child in page.get_children():
                    self.log_deletion(child.specific, user)
            self.log_deletion(page.specific, user)

            # this is a Page instance, so carry on as we were
            return super(Page, page).delete(*args, **kwargs)
        else:
            # retrieve an actual Page instance and delete that instead of page
            return DeletePageAction(Page.objects.get(id=page.id)).execute(*args, **kwargs)

    def execute(self, *args, **kwargs):
        return self._delete_page(self.page, *args, **kwargs)
