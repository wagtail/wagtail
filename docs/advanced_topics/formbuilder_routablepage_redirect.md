# How to use a redirect with Form builder to prevent double submission

It is common for form submission HTTP responses to be a `302 Found` temporary redirection to a new page.
By default `wagtail.contrib.forms.models.FormPage` success responses don't do this, meaning there is a risk that users will refresh the success page and re-submit their information.

Instead of rendering the `render_landing_page` content in the POST response, we will redirect to a `route` of the `FormPage` instance at a child URL path.
The content will still be managed within the same form page's admin.
This approach uses the additional contrib module `wagtail.contrib.routable_page`.

An alternative approach is to redirect to an entirely different page, which does not require the `routable_page` module.
See [](form_builder_custom_landing_page_redirect).

Make sure `"wagtail.contrib.routable_page"` is added to `INSTALLED_APPS`, see [](routable_page_mixin) documentation.

```python
from django.shortcuts import redirect

from wagtail.contrib.forms.models import AbstractEmailForm
from wagtail.contrib.routable_page.models import RoutablePageMixin, route


class FormPage(RoutablePageMixin, AbstractEmailForm):

    # fields, content_panels, …

    @route(r"^$")
    def index_route(self, request, *args, **kwargs):
        """Serve the form, and validate it on POST"""
        return super(AbstractEmailForm, self).serve(request, *args, **kwargs)

    def render_landing_page(self, request, form_submission, *args, **kwargs):
        """Redirect instead to self.thank_you route"""
        url = self.reverse_subpage("thank_you")
        # If a form_submission instance is available, append the ID to URL.
        if form_submission:
            url += "?id=%s" % form_submission.id
        return redirect(self.url + url, permanent=False)

    @route(r"^thank-you/$")
    def thank_you(self, request):
        """Return the superclass's landing page, after redirect."""
        form_submission = None
        try:
            submission_id = int(request.GET["id"])
        except (KeyError, TypeError):
            pass
        else:
            submission_class = self.get_submission_class()
            try:
                form_submission = submission_class.objects.get(id=submission_id)
            except submission_class.DoesNotExist:
                pass

        return super().render_landing_page(request, form_submission)
```
