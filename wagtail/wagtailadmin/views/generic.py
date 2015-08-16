from django.shortcuts import render
from django.views.generic.base import View

from wagtail.wagtailadmin.utils import permission_denied


class PermissionCheckedView(View):
    """
    Mixin for class-based views to enforce permission checks.
    Subclasses should set either of the following class properties:
    * permission_required (a single permission string)
    * any_permission_required (a list of permission strings - the user must have
      one or more of those permissions)
    """
    permission_required = None
    any_permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if self.permission_required is not None:
            if not request.user.has_perm(self.permission_required):
                return permission_denied(request)

        if self.any_permission_required is not None:
            has_permission = False

            for perm in self.any_permission_required:
                if request.user.has_perm(perm):
                    has_permission = True
                    break

            if not has_permission:
                return permission_denied(request)

        return super(PermissionCheckedView, self).dispatch(request, *args, **kwargs)


class IndexView(PermissionCheckedView):
    def get_queryset(self):
        return self.model.objects.all()

    def get(self, request):
        object_list = self.get_queryset()
        return render(request, self.template, {
            self.context_object_name: object_list,
        })
