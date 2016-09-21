=========================
Wagtail's release process
=========================

.. note::

    Based on Django's release process

Official releases
=================

Release numbering works as follows:

* Versions are numbered in the form ``A.B`` or ``A.B.C``.

* ``A.B`` is the *feature release* version number. Each version will be mostly
  backwards compatible with the previous release. Exceptions to this rule will
  be listed in the release notes.

* ``C`` is the *patch release* version number, which is incremented for bugfix
  and security releases. These releases will be 100% backwards-compatible with
  the previous patch release. The only exception is when a security or data
  loss issue can't be fixed without breaking backwards-compatibility. If this
  happens, the release notes will provide detailed upgrade instructions.

* Before a new feature release, we'll make at least one release candidate
  release. These are of the form ``A.BrcN``, which means the
  ``Nth`` release candidate of version ``A.B``.

In git, each Wagtail release will have a tag indicating its version number.
Additionally, each release series has its
own branch, called ``stable/A.B.x``, and bugfix/security releases will be
issued from those branches.

.. glossary::

  Feature release
    Feature releases (A.B, A.B+1, etc.) will happen roughly every month
    -- see `release process <#release-process>`__ for details. These releases will contain new
    features, improvements to existing features, and such.

  Patch release
    Patch releases (A.B.C, A.B.C+1, etc.) will be issued as needed, to fix
    bugs and/or security issues.

    These releases will be 100% compatible with the associated feature release,
    unless this is impossible for security reasons or to prevent data loss.
    So the answer to "should I upgrade to the latest patch release?" will always
    be "yes."

  Long-term support release
    Certain feature releases will be designated as long-term support (LTS)
    releases. These releases will get security and data loss fixes applied for
    a guaranteed period of time, typically six months.

..

.. note::

    I think long-term support release, should be really long-term (six months or more),
    but probably it will be hard to support this release because
    of frequent non-long-term releases.

Release cadence
===============

Wagtail uses a loose form of `semantic versioning <http://semver.org/>`_.
SemVer makes it easier to see at a glance how compatible releases are with each
other. It also helps to anticipate when compatibility shims will be removed.
It's not a pure form of SemVer as each feature release will continue to have a
few documented backwards incompatibilities where a deprecation path isn't
possible or not worth the cost.

Deprecation policy
==================

A feature release may deprecate certain features from previous releases. If a
feature is deprecated in feature release A.B, it will continue to work in
the following version but raise warnings. Feature deprecated in release A.B
will be removed in the A.B+2 release to ensure deprecations are done
over at least 2 feature releases.

So, for example, if we decided to start the deprecation of a function in
Wagtail 1.4:

* Wagtail 1.4 will contain a backwards-compatible replica of the function which
  will raise a ``RemovedInWagtail16Warning``.

* Wagtail 1.5 will still contain the backwards-compatible replica.

* Wagtail 1.6 will remove the feature outright.

The warnings are silent by default. You can turn on display of these warnings
with the ``python -Wd`` option.

A more generic example:

* X.0
* X.1
* X.2: Drop deprecation shims added in X.0.
* X.3: Drop deprecation shims added in X.1.
* X.4: Drop deprecation shims added in X.2.
* X.5 LTS: Drop deprecation shims added in X.3.
* X.6: Drop deprecation shims added in X.4.

.. note::

    Argh! It will be easier to understand and follow deprecation policy and versions compatibility, if LTS release will bump to the next “dot zero” version (X.0, X.1, X.2, X.3, X.4, X.5 (LTS), Z.0 and so on).

Supported versions
==================

At any moment in time, Wagtail's developer team will support a set of releases to
varying levels.

* The current development master will get new features and bug fixes
  requiring non-trivial refactoring.

* Patches applied to the master branch must also be applied to the last feature
  release branch, to be released in the next patch release of that feature
  series, when they fix critical problems:

  * Security issues.

  * Data loss bugs.

  * Crashing bugs.

  * Major functionality bugs in newly-introduced features.

  * Regressions from older versions of Wagtail.

  The rule of thumb is that fixes will be backported to the last feature
  release for bugs that would have prevented a release in the first place
  (release blockers).

* Security fixes and data loss bugs will be applied to the current master, the
  last two feature release branches, and any other supported long-term
  support release branches.

.. note::

    Probably we can start with "current master, the last feature release branch and
    supported long-term support release branch" because it's too hard to support.
    See an example below.

* Documentation fixes generally will be more freely backported to the last
  release branch. That's because it's highly advantageous to have the docs for
  the last release be up-to-date and correct, and the risk of introducing
  regressions is much less of a concern.


As a concrete example, consider a moment in time halfway between the release of
Wagtail 1.6 and 1.7. At this point in time:

* Features will be added to ``master``, to be released as Wagtail 1.7.

* Critical bug fixes will be applied to the ``stable/1.6.x`` branch, and
  released as 1.6.1, 1.6.2, etc.

* Security fixes and bug fixes for data loss issues will be applied to
  ``master`` and to the ``stable/1.6.x``, ``stable/1.5.x``, and
  ``stable/1.4.x`` (LTS) branches. They will trigger the release of ``1.6.1``,
  ``1.5.5``, ``1.4.8``, etc.

* Documentation fixes will be applied to master, and, if easily backported, to
  the latest stable branch, ``1.6.x``.

Supported versions of Django
============================

Each release of Wagtail declares which versions of Django it supports.

Typically new Wagtail feature release supports the last long-term support versions and
all following versions of Django.

For example, consider a moment in time before release of Wagtail 1.5
and after following releases:

 * Django 1.8 (LTS)
 * Django 1.9
 * Wagtail 1.4 (LTS) - Released before Django 1.10 and supports Django 1.8 and 1.9
 * Django 1.10

Wagtail 1.5 going to support Django 1.8 (LTS), 1.9, 1.10.
Wagtail 1.4 still support only Django 1.8 (LTS) and 1.9.

.. note::

    Would be great to put compatibility info (Django / Python) into
    index page of documentation, I think.

.. _release-process:

Release process
===============

Wagtail uses a time-based release schedule, with feature releases every month or so.

After each feature release, the release manager will announce a timeline for
the next feature release.

Release cycle
-------------

Each release cycle consists of three parts:

Phase one: feature proposal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first phase of the release process will include figuring out what major
features to include in the next version. This should include a good deal of
preliminary work on those features -- working code trumps grand design.

.. note::

    Would be good to have Roadmap page shared with community.

Phase two: development
~~~~~~~~~~~~~~~~~~~~~~

The second part of the release schedule is the "heads-down" working period.
Using the roadmap produced at the end of phase one, we'll all work very hard to
get everything on it done.

At the end of phase two, any unfinished features will be postponed until the
next release.

At this point, the ``stable/A.B.x`` branch will be forked from ``master``.

.. note::

    What about alpha release in the end of this phase?


Phase three: bugfixes
~~~~~~~~~~~~~~~~~~~~~

The last part of a release cycle is spent fixing bugs -- no new features will
be accepted during this time.

The release candidate marks the string freeze.
After this point, new translatable strings must not be added.

.. note::

    Hm... What about string freeze? Django freezes string at least two weeks before the final release.

During this phase, committers will be more and more conservative with
backports, to avoid introducing regressions. After the release candidate, only
release blockers and documentation fixes should be backported.

In parallel to this phase, ``master`` can receive new features, to be released
in the ``A.B+1`` cycle.

Bug-fix releases
----------------

After a feature release (e.g. A.B), the previous release will go into bugfix
mode.

The branch for the previous feature release (e.g. ``stable/A.B-1.x``) will
include bugfixes. Critical bugs fixed on master must *also* be fixed on the
bugfix branch; this means that commits need to cleanly separate bug fixes from
feature additions. The developer who commits a fix to master will be
responsible for also applying the fix to the current bugfix branch.