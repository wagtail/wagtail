# -*- coding: utf-8 -*-
from django.db import migrations
from django.db.models import Count, Q
from wagtail.models import Page as RealPage


def ancestor_of_q(page):
    paths = [page.path[0:pos] for pos in range(0, len(page.path) + 1, page.steplen)[1:]]
    q = Q(path__in=paths)

    return q


def create_default_workflows(apps, schema_editor):
    # This will recreate the existing publish-permission based moderation setup in the new workflow system, by creating new workflows

    # Get models
    ContentType = apps.get_model("contenttypes.ContentType")
    Workflow = apps.get_model("wagtailcore.Workflow")
    GroupApprovalTask = apps.get_model("wagtailcore.GroupApprovalTask")
    GroupPagePermission = apps.get_model("wagtailcore.GroupPagePermission")
    WorkflowPage = apps.get_model("wagtailcore.WorkflowPage")
    WorkflowTask = apps.get_model("wagtailcore.WorkflowTask")
    Page = apps.get_model("wagtailcore.Page")
    Group = apps.get_model("auth.Group")

    # Get this from real page model just in case it has been overridden
    Page.steplen = RealPage.steplen

    # Create content type for GroupApprovalTask model
    group_approval_content_type, __ = ContentType.objects.get_or_create(
        model="groupapprovaltask", app_label="wagtailcore"
    )

    publish_permissions = GroupPagePermission.objects.filter(permission_type="publish")

    for permission in publish_permissions:
        # find groups with publish permission over this page or its ancestors (and therefore this page by descent)
        page = permission.page
        page = Page.objects.get(pk=page.pk)
        ancestors = Page.objects.filter(ancestor_of_q(page))
        ancestor_permissions = publish_permissions.filter(page__in=ancestors)
        groups = Group.objects.filter(
            Q(page_permissions__in=ancestor_permissions)
            | Q(page_permissions__pk=permission.pk)
        ).distinct()

        # get a GroupApprovalTask with groups matching these publish permission groups (and no others)
        task = (
            GroupApprovalTask.objects.filter(groups__id__in=groups.all())
            .annotate(count=Count("groups"))
            .filter(count=groups.count())
            .filter(active=True)
            .first()
        )
        if not task:
            # if no such task exists, create it
            group_names = " ".join([group.name for group in groups])
            task = GroupApprovalTask.objects.create(
                name=group_names + " approval",
                content_type=group_approval_content_type,
                active=True,
            )
            task.groups.set(groups)

        # get a Workflow containing only this task if if exists, otherwise create it
        workflow = (
            Workflow.objects.annotate(task_number=Count("workflow_tasks"))
            .filter(task_number=1)
            .filter(workflow_tasks__task=task)
            .filter(active=True)
            .first()
        )
        if not workflow:
            workflow = Workflow.objects.create(name=task.name, active=True)

            WorkflowTask.objects.create(
                workflow=workflow,
                task=task,
                sort_order=0,
            )

        # if the workflow is not linked by a WorkflowPage to the permission's linked page, link it by creating a new WorkflowPage now
        if not WorkflowPage.objects.filter(workflow=workflow, page=page).exists():
            WorkflowPage.objects.create(workflow=workflow, page=page)


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0047_add_workflow_models"),
    ]

    operations = [
        migrations.RunPython(create_default_workflows, migrations.RunPython.noop),
    ]
