# Wagtail's release process

## Official releases

Release numbering works as follows:

-   Versions are numbered in the form `A.B` or `A.B.C`.

-   `A.B` is the _feature release_ version number. Each version will be mostly
    backwards compatible with the previous release. Exceptions to this rule
    will be listed in the release notes. When `B` is `0`, the release contains
    backwards-incompatible changes.

-   `C` is the _patch release_ version number, which is incremented for bugfix
    and security releases. These releases will be 100% backwards-compatible with
    the previous patch release. The only exception is when a security or data
    loss issue can't be fixed without breaking backwards-compatibility. If this
    happens, the release notes will provide detailed upgrade instructions.

-   Before a new feature release, we'll make at least one release candidate
    release. These are of the form `A.BrcN`, which means the
    `Nth` release candidate of version `A.B`.

In git, each Wagtail release will have a tag indicating its version number.
Additionally, each release series has its
own branch, called `stable/A.B.x`, and bugfix/security releases will be
issued from those branches.

For more information about how Wagtail issues new releases for security purposes, please see our [security policies](https://docs.wagtail.org/en/latest/contributing/security.html).

**Feature release**

Feature releases (A.B, A.B+1, etc.) happen every three months
-- see [release schedule](release_schedule) for details. These releases will contain new
features and improvements to existing features.

**Patch release**

Patch releases (A.B.C, A.B.C+1, etc.) will be issued as needed, to fix
bugs and/or security issues.

These releases will be 100% compatible with the associated feature release,
unless this is impossible for security reasons or to prevent data loss.
So the answer to "should I upgrade to the latest patch release?" will always
be "yes."

A feature release will usually stop receiving patch release updates when the next feature release comes out.

**Long-term support (LTS) release**

Certain feature releases will be designated as long-term support releases. These
releases will get security and data loss fixes applied for a guaranteed period
of time. Typically, a long-term support release will happen once every four feature releases and receive updates for six feature releases, giving a support
period of eighteen months with a six month overlap.

Also, long-term support releases will ensure compatibility with at least one
[Django long-term support release](https://www.djangoproject.com/download/#supported-versions).

**Major release**

Certain feature releases (A.0, A+1.0, etc.) will be designated as major
releases, marked by incrementing the first part of the version number. These
releases will contain significant changes to the user interface or
backwards-incompatible changes.

Major releases do not happen on a regular schedule. Typically, they will happen
when the previous feature releases have accumulated enough deprecated features
that it's time to remove them.

(deprecation_policy)=

## Deprecation policy

Wagtail uses a loose form of [semantic versioning](https://semver.org/).
SemVer makes it easier to see at a glance how compatible releases are with each
other. It also helps to anticipate when compatibility shims will be removed.

It's not a pure form of SemVer as each feature release will continue to have a
few documented backwards incompatibilities where a deprecation path isn't
possible or not worth the cost. This is especially true for features documented
under the [](../extending/index) section of the documentation and their
corresponding API reference, which tend to be more actively developed.

We try to strike the balance between:

-   keeping the API stable for most users,
-   documenting features for advanced developers and third-party package maintainers, and
-   allowing for continuous improvement of Wagtail's internals.

A feature release may deprecate certain features from previous releases. If a
feature is deprecated in feature release A.x, it will continue to work in all
A.x versions (for all versions of x) but raise warnings. Deprecated features
will be removed in the A+1.0 release, or A+2.0 for features deprecated in the
last A.x feature release to ensure deprecations are done over at least 2
feature releases.

For example:

-   Wagtail 5.1 was released. Function `func_a()` that entered deprecation in
    this version would have a backwards-compatible replica which would raise a
    `RemovedInWagtail60Warning`.

-   Wagtail 5.2 was released. This version still contained the
    backwards-compatible replica of `func_a()`. Future version numbers are
    provisional, so the next version could either be 5.3 or 6.0. For function
    `func_b()` that entered deprecation in version 5.2, it would tentatively
    raise a `RemovedInWagtail60Warning`.

-   Wagtail 6.0 was decided to be the next version after Wagtail 5.2. In
    this release, `func_a()` was outright removed, and `func_b()` would raise a
    `RemovedInWagtail70Warning` instead.

-   When Wagtail 7.0 is released (after all 6.x versions), `func_b()` will be
    removed.

The warnings are silent by default. You can turn on display of these warnings
with the `python -Wd` option.

## Supported versions

At any moment in time, Wagtail's developer team will support a set of releases to
varying levels.

-   The current development `main` will get new features and bug fixes
    requiring non-trivial refactoring.

-   Patches applied to the `main` branch must also be applied to the last feature
    release branch, to be released in the next patch release of that feature
    series, when they fix critical problems:

    -   Security issues.

    -   Data loss bugs.

    -   Crashing bugs.

    -   Major functionality bugs in newly-introduced features.

    -   Regressions from older versions of Wagtail.

    The rule of thumb is that fixes will be backported to the last feature
    release for bugs that would have prevented a release in the first place
    (release blockers).

-   Security fixes and data loss bugs will be applied to the current `main`, the
    last feature release branch, and any other supported long-term
    support release branches.

-   Documentation fixes generally will be more freely backported to the last
    release branch. That's because it's highly advantageous to have the docs for
    the last release be up-to-date and correct, and the risk of introducing
    regressions is much less of a concern.

As a concrete example, consider a moment in time halfway between the release of
Wagtail 6.1 and 6.2. At this point in time:

-   Features will be added to `main`, to be released as Wagtail 6.2.

-   Critical bug fixes will be applied to the `stable/6.1.x` branch, and
    released as 6.1.1, 6.1.3, etc.

-   Security fixes and bug fixes for data loss issues will be applied to
    `main` and to the `stable/6.1.x` and `stable/5.2.x` (LTS) branches.
    They will trigger the release of `6.1.3`, `5.2.6`, etc.

-   Documentation fixes will be applied to `main`, and, if easily backported, to
    the latest stable branch, `stable/6.1.x`.

## Supported versions of Django

Each release of Wagtail declares which versions of Django it supports.

Typically, a new Wagtail feature release supports the last long-term support version and
all following versions of Django.

For example, consider a moment in time before the release of Wagtail 6.3 and
after the following releases:

-   Django 4.2 (LTS)
-   Django 5.0
-   Wagtail 6.2 - Released before Django 5.1 and supports Django 4.2 and 5.0
-   Django 5.1

Wagtail 6.3 will support Django 4.2 (LTS), 5.0, 5.1.
Wagtail 6.2 will still support only Django 4.2 (LTS) and 5.0.

In some cases, the latest Wagtail feature release falls in between the beta and
final release of a new Django version. In such cases, the Wagtail release may
add official support for the new Django version in a patch release. An example
of this was Wagtail 5.2, which added support for Django 5.0 in Wagtail 5.2.2.

For a list of supported Django and Python versions for each Wagtail release, see the [](compatible_django_python_versions) table.

(release_schedule)=

## Release schedule

Wagtail uses a [time-based release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule),
with feature releases every three months.

### Release cycle

Each release cycle consists of three parts:

#### Phase one: roadmap update

The first phase of the release process will include figuring out what major
features to include in the next version. This should include a good deal of
preliminary work on those features -- working code trumps grand design.

The development team will announce a roadmap update for the next feature
release in the form of a request for comments (RFC) to
[Wagtail's RFCs repository](https://github.com/wagtail/rfcs). Anyone is welcome
and encouraged to comment on the RFC. After the RFC is approved by the
[Wagtail core team](https://wagtail.org/core-team/), the roadmap update will be
available on [wagtail.org/roadmap](https://wagtail.org/roadmap).

#### Phase two: development

The second part of the release schedule is the "heads-down" working period.
Using the roadmap produced at the end of phase one, we'll all work very hard to
get everything on it done.

At the end of phase two, any unfinished features will be postponed until the
next release.

At this point, the `stable/A.B.x` branch will be forked from `main`.

#### Phase three: bugfixes

The last part of a release cycle is spent fixing bugs -- no new features will
be accepted during this time.

Once all known blocking bugs have been addressed, a release candidate will be
made available for testing. The final release will usually follow two weeks later,
although this period may be extended if the further release blockers are found.

During this phase, committers will be more and more conservative with
backports, to avoid introducing regressions. After the release candidate, only
release blockers and documentation fixes should be backported.

Developers should avoid adding any new translatable strings after the release
candidate - this ensures that translators have the full period between the release
candidate and the final release to bring translations up to date. Translations
will be re-imported immediately before the final release.

In parallel to this phase, `main` can receive new features, to be released
in the `A.B+1` cycle.

### Patch releases

After a feature release `A.B`, the previous release will go into security
support mode.

The branches for the current feature release `stable/A.B.x` and the last LTS release will receive critical bug, security, and data loss fixes.

The branch for the previous feature release `stable/A.B-1.x` will only include security and data loss fixes.

Bugs fixed on `main` must _also_ be fixed on other applicable branches; this
means that commits need to cleanly separate bug fixes from feature additions.
The developer who commits a fix to `main` will be responsible for also applying
the fix to the respective branches.

## Acknowledgement

This release process is based on [](inv:django#internals/release-process).
