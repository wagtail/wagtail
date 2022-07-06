# Wagtail's release process

## Official releases

Release numbering works as follows:

-   Versions are numbered in the form `A.B` or `A.B.C`.

-   `A.B` is the _feature release_ version number. Each version will be mostly
    backwards compatible with the previous release. Exceptions to this rule will
    be listed in the release notes.

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

**Feature release**

Feature releases (A.B, A.B+1, etc.) happen every three months
-- see [release process](release-process) for details. These releases will contain new
features and improvements to existing features.

**Patch release**

Patch releases (A.B.C, A.B.C+1, etc.) will be issued as needed, to fix
bugs and/or security issues.

These releases will be 100% compatible with the associated feature release,
unless this is impossible for security reasons or to prevent data loss.
So the answer to "should I upgrade to the latest patch release?" will always
be "yes."

**Long-term support release**

Certain feature releases will be designated as long-term support (LTS)
releases. These releases will get security and data loss fixes applied for
a guaranteed period of time, typically six months.

## Release cadence

Wagtail uses a loose form of [semantic versioning](https://semver.org/).
SemVer makes it easier to see at a glance how compatible releases are with each
other. It also helps to anticipate when compatibility shims will be removed.
It's not a pure form of SemVer as each feature release will continue to have a
few documented backwards incompatibilities where a deprecation path isn't
possible or not worth the cost.

## Deprecation policy

A feature release may deprecate certain features from previous releases. If a
feature is deprecated in feature release A.B, it will continue to work in
the following version but raise warnings. Features deprecated in release A.B
will be removed in the A.B+2 release to ensure deprecations are done
over at least 2 feature releases.

So, for example, if we decided to start the deprecation of a function in
Wagtail 1.4:

-   Wagtail 1.4 will contain a backwards-compatible replica of the function which
    will raise a `RemovedInWagtail16Warning`.

-   Wagtail 1.5 will still contain the backwards-compatible replica.

-   Wagtail 1.6 will remove the feature outright.

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
Wagtail 1.6 and 1.7. At this point in time:

-   Features will be added to `main`, to be released as Wagtail 1.7.

-   Critical bug fixes will be applied to the `stable/1.6.x` branch, and
    released as 1.6.1, 1.6.2, etc.

-   Security fixes and bug fixes for data loss issues will be applied to
    `main` and to the `stable/1.6.x` and `stable/1.4.x` (LTS) branches.
    They will trigger the release of `1.6.1`, `1.4.8`, etc.

-   Documentation fixes will be applied to `main`, and, if easily backported, to
    the latest stable branch, `1.6.x`.

## Supported versions of Django

Each release of Wagtail declares which versions of Django it supports.

Typically, a new Wagtail feature release supports the last long-term support version and
all following versions of Django.

For example, consider a moment in time before release of Wagtail 1.5
and after the following releases:

-   Django 1.8 (LTS)
-   Django 1.9
-   Wagtail 1.4 (LTS) - Released before Django 1.10 and supports Django 1.8 and 1.9
-   Django 1.10

Wagtail 1.5 will support Django 1.8 (LTS), 1.9, 1.10.
Wagtail 1.4 will still support only Django 1.8 (LTS) and 1.9.

(release-process)=

## Release process

Wagtail uses a [time-based release schedule](https://github.com/wagtail/wagtail/wiki/Release-schedule),
with feature releases every three months.

After each feature release, the release manager will announce a timeline for
the next feature release.

### Release cycle

Each release cycle consists of three parts:

#### Phase one: feature proposal

The first phase of the release process will include figuring out what major
features to include in the next version. This should include a good deal of
preliminary work on those features -- working code trumps grand design.

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

### Bug-fix releases

After a feature release (e.g. A.B), the previous release will go into bugfix
mode.

The branch for the previous feature release (e.g. `stable/A.B-1.x`) will
include bugfixes. Critical bugs fixed on `main` must _also_ be fixed on the
bugfix branch; this means that commits need to cleanly separate bug fixes from
feature additions. The developer who commits a fix to `main` will be
responsible for also applying the fix to the current bugfix branch.
