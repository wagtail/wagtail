from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test
from wagtail.contrib.forms.views import SubmissionsListView


def user_is_called_bob(user):
    return user.first_name == 'Bob'


@user_passes_test(user_is_called_bob)
def bob_only_zone(request):
    return HttpResponse("Bobs of the world unite!")


def message_test(request):
    if request.method == 'POST':
        fn = getattr(messages, request.POST['level'])
        fn(request, request.POST['message'])
        return redirect('testapp_message_test')
    else:
        return TemplateResponse(request, 'wagtailadmin/base.html')


class CustomSubmissionsListView(SubmissionsListView):
    paginate_by = 50
    ordering = ('submit_time',)
    ordering_csv = ('-submit_time',)

    def get_csv_filename(self):
        """ Returns the filename for CSV file with page title at start"""
        filename = super().get_csv_filename()
        return self.form_page.slug + '-' + filename
