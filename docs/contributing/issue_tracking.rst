Issue tracking
==============

We welcome bug reports, feature requests and pull requests through Wagtail's `Github issue tracker <https://github.com/wagtail/wagtail/issues>`_.

Issues
------

An issue must always correspond to a specific action with a well-defined completion state: fixing a bug, adding a new feature, updating documentation, cleaning up code. Open-ended issues where the end result is not immediately clear ("come up with a way of doing translations") are fine, as long as there's a clear way to progress the issue and identify when it has been completed (not e.g. "make rich text fields suck less").

Do not use issues for support queries or other questions ("How do I do X?" - although "Implement a way of doing X" or "Document how to do X" could well be valid issues). These should go on the `Wagtail Support Google group <https://groups.google.com/forum/#!forum/wagtail>`_.

As soon as a ticket is opened - ideally within one day - a member of the core team will give it an initial classification, by either closing it as invalid or assigning it to a milestone. Don't be discouraged if you feel that your ticket has been given a lower priority than it deserves - this decision isn't permanent. We will consider all feedback, and reassign or reopen tickets where appropriate.

(From the other side, this means that the core team member doing the classification should feel free to make bold unilateral decisions - there's no need to seek consensus first. If they make the wrong judgment call, that can always be reversed later.)

The possible milestones that it might be assigned to are as follows:

* **invalid** (closed): this issue doesn't identify a specific action to be taken, or the action is not one that we want to take. For example - a bug report for something that's working as designed, or a feature request for something that's actively harmful.
* **some-day**: the issue is accepted as valid (i.e. it's a bug report for a legitimate bug, or a useful feature request) but not deemed a priority to work on (in the opinion of the core team). For example - a bug that's only cosmetic, or a feature that would be kind of neat but not really essential. Feel free to take it on!
* **real-soon-now**: the issue is considered important by the core team (roughly speaking: it's a bug or missing feature that's causing headaches for people) but isn't necessarily going to be completed on any set timescale. Feel free to take it on!
* A specific version number: the issue is important enough that it needs to be fixed in this version.

On some occasions it may take longer for the core team to classify an issue into a milestone. For example:

* It may require a non-trivial amount of work to confirm the presence of a bug. In this case, feedback and further details from other contributors, whether or not they can replicate the bug, would be particularly welcomed.
* It may require further discussion to decide whether the proposal is a good idea or not - if so, it will be tagged "design decision needed".

We will endeavour to make sure that issues don't remain in this state for prolonged periods. Issues and PRs tagged "design decision needed" will be revisited regularly and discussed with at least two core contributors - we aim to review each ticket at least once per release cycle (= 6 weeks).

Pull requests
-------------

As with issues, the core team will classify pull requests as soon as they are opened, usually within one day. Unless the change is invalid or particularly contentious (in which case it will be closed or marked as "design decision needed"), it will generally be classified under the next applicable version - the next minor release for new features, or the next patch release for bugfixes - and marked as 'Needs review'. All contributors, core and non-core, are invited to offer feedback on the pull request.

Subsequently (ideally within a week or two, but possibly longer for larger submissions) a core team member will merge it if it is ready to be merged, or tag it as requiring further work ('needs work' / 'needs tests' / 'needs docs'). In the latter case, they may also reassign it to a later milestone ('real-soon-now' or 'some-day'). Pull requests that require further work are handled and prioritised in the same way as issues - anyone is welcome to pick one up from the backlog, whether or not they were the original committer.

Release schedule
----------------

We aim to release a new version every 2 months. To keep to this schedule, we will tend to 'bump' issues and PRs to a future release where necessary, rather than let them delay the present one. For this reason, an issue being tagged under a particular release milestone should not be taken as any kind of guarantee that the feature will actually be shipped in that release.

