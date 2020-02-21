The Dashboard
~~~~~~~~~~~~~

.. MAKE CHANGES TO INCLUDE MODERATION//

The Dashboard provides information on:

* The number of pages, images, and documents currently held in the Wagtail CMS
* Any pages currently awaiting moderation (if you have these privileges)
* Any pages that you've locked (if your administrator has enabled :ref:`author-specific locking<WAGTAILADMIN_GLOBAL_PAGE_EDIT_LOCK>`)
* Your most recently edited pages

You can return to the Dashboard at any time by clicking the Wagtail logo in the top-left of the screen.

.. image:: ../../_static/images/screen02_dashboard_editor.png

- Clicking the logo returns you to your Dashboard.
- The stats at the top of the page describe the total amount of content on the CMS (just for fun!).

- The *Your pages in workflow moderation* table shows you any pages in moderation that you own or submitted for moderation yourself, along with which
  moderation tasks they are currently on.

- The *Pages you can moderate* table will only be displayed if you are able to perform moderation actions.

  - Clicking the name of a page will take you to the ‘Edit page’ interface for this page.
  - Clicking approve or reject will either progress the page to the next task in the moderation workflow (or publish if it's the final stage) or return the page to draft status. An email will be sent to the creator of the page giving the result of the overall workflow when it completes.
  - The *Task* column shows which moderation task the page is currently in, and the *Task started* column when it

- The *Your locked pages* table shows the pages you've locked so that only you can edit them.
- The *Locked At* column displays the date you locked the page.
- Clicking the name of a page will take you to the ‘Edit page’ interface for this page.
- Clicking *See all locked pages* will take you to the *Locked Pages* Report, showing the pages locked by any user

- The *Your most recent edits* table displays the five pages that you most recently edited.
- The date column displays the date that you edited the page. Hover your mouse over the date for a more exact time/date.
- The status column displays the current status of the page. A page will have one of three statuses:

  - Live: Published and accessible to website visitors
  - Draft:  Not live on the website.
  - Live + Draft: A version of the page is live, but a newer version is in draft mode.
