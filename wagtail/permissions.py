from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy, override_permission_policy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy

page_permission_policy = override_permission_policy("page", PagePermissionPolicy(Page))
site_permission_policy = override_permission_policy("site", ModelPermissionPolicy(Site))
collection_permission_policy = override_permission_policy("collection", CollectionManagementPermissionPolicy(Collection))
task_permission_policy = override_permission_policy("task", ModelPermissionPolicy(Task))
workflow_permission_policy = override_permission_policy("workflow", ModelPermissionPolicy(Workflow))
locale_permission_policy = override_permission_policy("locale", ModelPermissionPolicy(Locale))
