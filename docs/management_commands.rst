Management commands
===================

publish_scheduled_pages
-----------------------

:code:`./manage.py publish_scheduled_pages`

This command publishes or unpublishes pages that have had these actions scheduled by an editor. It is recommended to run this command once an hour.

fixtree
-------

:code:`./manage.py fixtree`

This command scans for errors in your database and attempts to fix any issues it finds.

move_pages
----------

:code:`manage.py move_pages from to`

This command moves a selection of pages from one section of the tree to another.

Options:

 - **from**
  This is the **id** of the page to move pages from. All descendants of this page will be moved to the destination. After the operation is complete, this page will have no children.

 - **to**
  This is the **id** of the page to move pages to.

update_index
------------

:code:`./manage.py update_index`

This command rebuilds the search index from scratch. It is only required when using Elasticsearch.

It is recommended to run this command once a week and at the following times:

 - whenever any pages have been created through a script (after an import, for example)
 - whenever any changes have been made to models or search configuration

The search may not return any results while this command is running, so avoid running it at peak times.

search_garbage_collect
----------------------

:code:`./manage.py search_garbage_collect`

Wagtail keeps a log of search queries that are popular on your website. On high traffic websites, this log may get big and you may want to clean out old search queries. This command cleans out all search query logs that are more than one week old.
