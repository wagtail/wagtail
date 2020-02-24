Managing Workflows
==================

Workflows allow you to configure how moderation works on your site. Workflows are sequences of tasks, all of which must be approved
before the workflow completes (by default, this results in the publication of the page, but depends on your site settings TODO: add settings link).

The workflow management interface is accessed via the `Workflows` item in the `Settings` submenu, found in the left menu bar.

TODO: add screenshot

In this interface you can see all of the workflows on your site, and the order of tasks in each. You can click on a workflow to edit it or to assign it
to part of the page tree, or use the `Add a workflow` button to create a new workflow.


Editing workflows
_________________


TODO: add screenshot

Under `Tasks`, you can add, remove, or reorder tasks in a workflow. You may also disable the workflow, which will cancel all pages currently
in moderation on this workflow, and prevent others from starting it.

Under `Pages`, you can see a list of the pages to which the workflow has been assigned: any child pages will also have the same workflow, 
so if a workflow is assigned to the root page, it becomes the default workflow. You may remove it from pages using the `Remove` button to
the right of each entry, or assign it to a page using the `Add to page` button.


Creating and editing tasks
__________________________

TODO: add screenshot

In the tasks interface, accessible via the `Tasks` button in the upper right corner of the workflow management interface, you can see a list of the tasks
currently available. Similarly to workflows, you can click an existing task to edit it, or the `Add a task` button to create a new task.

When creating a task, if you have multiple task types available, these will be offered as options. By default, only `group approval tasks` are available.
Creating a `group approval task`, you will be able to select one or multiple groups: members of any of these, as well as administrators, will be able to
approve or reject moderation for this task.

When editing a task, you may find that some fields - including the groups in a `group approval task` are uneditable. This is to ensure workflow history
remains consistent - if you find yourself needing to change the group, it is recommended that you disable the old task, and create a new one with the groups
you need. Disabling a task will cause any pages currently in moderation on that task to skip to the next task.