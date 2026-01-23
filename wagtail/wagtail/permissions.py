from wagtail.models import Collection, Locale, Page, Site, Task, Workflow
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.collections import CollectionManagementPermissionPolicy
from wagtail.permission_policies.pages import PagePermissionPolicy

page_permission_policy = PagePermissionPolicy(Page)
site_permission_policy = ModelPermissionPolicy(Site)
collection_permission_policy = CollectionManagementPermissionPolicy(Collection)
task_permission_policy = ModelPermissionPolicy(Task)
workflow_permission_policy = ModelPermissionPolicy(Workflow)
locale_permission_policy = ModelPermissionPolicy(Locale)
