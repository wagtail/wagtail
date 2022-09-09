# Previewing and submitting pages for moderation

The Save/Submit for moderation menu is always present at the bottom of the page edit/creation screen. The menu allows you to perform the following actions, dependent on whether you are an editor, moderator or administrator:

-   **Save draft:** Saves your current changes but doesn't submit the page for moderation and so won’t be published. (all roles)
-   **Submit to Moderators approval:** Saves your current changes and submits the page for moderation. The page will then enter a moderation workflow: a set of tasks which, when all are approved, will publish the page (by default, depending on your site {ref}`settings<workflow_settings>`). This button may be missing if the site administrator has {ref}`disabled moderation<wagtail_moderation_enabled>`, or hasn't assigned a workflow to this part of the site. (all roles)
-   **Publish/Unpublish:** Clicking the _Publish_ button will publish this page. Clicking the _Unpublish_ button will take you to a confirmation screen asking you to confirm that you wish to unpublish this page. If a page is published it will be accessible from its specific URL and will also be displayed in site search results. (moderators and administrators only)

![Page editor, with Save/Submit menu expanded to reveal all four options](../../_static/images/screen13_publish_menu.png)

Other common page actions are available in the **Actions** dropdown, at the top of the screen.

## Page previews

To access Wagtail’s page preview, head over to the Preview side panel. A live-updating preview shows to the right of the page in Mobile mode, and it can be opened in a new tab displaying the page as it would look if published.

![Page editor for "Bread and Circuses" page. The form to the left, and to the right the Preview side panel is expanded, showing the page as it would appear to users on Mobile devices](../../_static/images/screen13_preview_panel.png)
