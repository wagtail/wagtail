===============
Committing code
===============

This section is for the committers of Wagtail,
or for anyone interested in the process of getting code committed to Wagtail.

Code should only be committed after it has been reviewed
by at least one other reviewer or committer,
unless the change is a small documentation change or fixing a typo.
If additional code changes are made after the review, it is OK to commit them
without further review if they are uncontroversial and small enough that
there is minimal chance of introducing new bugs.

Most code contributions will be in the form of pull requests from Github.
Pull requests should not be merged from Github, apart from small documentation fixes,
which can be merged with the 'Squash and merge' option. Instead, the code should
be checked out by a committer locally, the changes examined and rebased,
the ``CHANGELOG.txt`` and release notes updated,
and finally the code should be pushed to the master branch.
This process is covered in more detail below.

Check out the code locally
==========================

If the code has been submitted as a pull request,
you should fetch the changes and check them out in your Wagtail repository.
A simple way to do this is by adding the following ``git`` alias to your ``~/.gitconfig`` (assuming ``upstream`` is ``wagtail/wagtail``):

.. code-block:: text

    [alias]
        pr = !sh -c \"git fetch upstream pull/${1}/head:pr/${1} && git checkout pr/${1}\"

Now you can check out pull request number ``xxxx`` by running ``git pr xxxx``.

Rebase on to master
===================

Now that you have the code, you should rebase the commits on to the ``master`` branch.
Rebasing is preferred over merging,
as merge commits make the commit history harder to read for small changes.

You can fix up any small mistakes in the commits,
such as typos and formatting, as part of the rebase.
``git rebase --interactive`` is an excellent tool for this job.

Ideally, use this as an opportunity to squash the changes to a few commits, so
each commit is making a single meaningful change (and not breaking anything).
If this is not possible because of the nature of the changes, it's acceptable
to either squash into a commit or leave all commits unsquashed,
depending on which will be more readable in the commit history.

.. code-block:: console

    $ # Get the latest commits from Wagtail
    $ git fetch upstream
    $ git checkout master
    $ git merge --ff-only upstream/master
    $ # Rebase this pull request on to master
    $ git checkout pr/xxxx
    $ git rebase master
    $ # Update master to this commit
    $ git checkout master
    $ git merge --ff-only pr/xxxx

Update ``CHANGELOG.txt`` and release notes
==========================================

Every significant change to Wagtail should get an entry in the ``CHANGELOG.txt``,
and the release notes for the current version.

The ``CHANGELOG.txt`` contains a short summary of each new feature, refactoring, or bug fix in each release.
Each summary should be a single line.
Bug fixes should be grouped together at the end of the list for each release,
and be prefixed with "Fix:".
The name of the contributor should be added at the end of the summary,
in brackets, if they are not a core committer.
For example:

.. code-block:: text

     * Fix: Tags added on the multiple image uploader are now saved correctly (Alex Smith)

The release notes for each version contain a more detailed description of each change.
Backwards compatibility notes should also be included.
Large new features or changes should get their own section,
while smaller changes and bug fixes should be grouped together in their own section.
See previous release notes for examples.
The release notes for each version are found in ``docs/releases/x.x.x.rst``.

If the contributor is a new person, and this is their first contribution to Wagtail,
they should be added to the ``CONTRIBUTORS.rst`` list.
Contributors are added in chronological order,
with new contributors added to the bottom of the list.
Use their preferred name.
You can usually find the name of a contributor on their Github profile.
If in doubt, or if their name is not on their profile, ask them how they want to be named.

If the changes to be merged are small enough to be a single commit,
amend this single commit with the additions to
the ``CHANGELOG.txt``, release notes, and contributors:

.. code-block:: console

    $ git add CHANGELOG.txt docs/releases/x.x.x.rst CONTRIBUTORS.rst
    $ git commit --amend --no-edit

If the changes do not fit in a single commit, make a new commit with the updates to
the ``CHANGELOG.txt``, release notes, and contributors.
The commit message should say ``Release notes for #xxxx``:

.. code-block:: console

    $ git add CHANGELOG.txt docs/releases/x.x.x.rst CONTRIBUTORS.rst
    $ git commit -m 'Release notes for #xxxx'

Push to master
==============

The changes are ready to be pushed to ``master`` now.

.. code-block:: console

    $ # Check that everything looks OK
    $ git log upstream/master..master --oneline
    $ git push --dry-run upstream master
    $ # Push the commits!
    $ git push upstream master
    $ git branch -d pr/xxxx

When you have made a mistake
============================

It's ok! Everyone makes mistakes. If you realise that recent merged changes
have a negative impact, create a new pull request with a revert of the changes
and merge it without waiting for a review. The PR will serve as additional
documentation for the changes, and will run through the CI tests.
