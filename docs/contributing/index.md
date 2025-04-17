# Contributing

Thank you for your interest in improving Wagtail!

## First-time contributors

1. Read this document first.
2. We don’t assign tasks. Feel free to pick any issue/task that isn’t already being worked on by someone else.
3. Read the [Your first contribution guide](first_contribution_guide).

## Issues

The easiest way to contribute to Wagtail is to tell us how to improve it! First, check to see if your bug or feature request has already been submitted at [github.com/wagtail/wagtail/issues](https://github.com/wagtail/wagtail/issues). If it has, and you have some supporting information that may help us deal with it, comment on the existing issue. If not, please [create a new one](https://github.com/wagtail/wagtail/issues/new), providing as much relevant context as possible. For example, if you're experiencing problems with installation, detail your environment and the steps you've already taken. If something isn't displaying correctly, tell us what browser you're using, and include a screenshot if possible.

If your bug report is a security issue, **do not** report it with an issue. Please read our guide to [reporting security issues](security).

```{toctree}
:maxdepth: 2

issue_tracking
```

## Pull requests

If you are just getting started with development and have never contributed to an open-source project, we recommend you read the [Your first contribution guide](first_contribution_guide). If you're a confident Python or Django developer, [fork it](https://github.com/wagtail/wagtail/) and read the [developing docs](developing_for_wagtail) to get stuck in!

We welcome all contributions, whether they solve problems that are specific to you or they address existing issues. If you're stuck for ideas, pick something from the [issue list](https://github.com/wagtail/wagtail/issues?q=is%3Aopen), or email us directly at [hello@wagtail.org](mailto:hello@wagtail.org) if you'd like us to suggest something!

For large-scale changes, we'd generally recommend breaking them down into smaller pull requests that achieve a single well-defined task and can be reviewed individually. If this isn't possible, we recommend opening a pull request on the [Wagtail RFCs](https://github.com/wagtail/rfcs/) repository, so that there's a chance for the community to discuss the change before it gets implemented.

```{toctree}
:maxdepth: 2

first_contribution_guide
developing
```

## Translations

Wagtail has internationalization support so if you are fluent in a non-English language you can contribute by localizing the interface.

Translation work should be submitted through [Transifex](https://explore.transifex.com/torchbox/wagtail/), for information on how to get started see [](contributing_translations).

(other_contributions)=

## Other contributions

We welcome contributions to all aspects of Wagtail. If you would like to improve the design of the user interface, or extend the documentation, please submit a pull request as above. Here are some other ways to contribute if you are getting started or have been using Wagtail for a long time but are unable to contribute code.

-   Contribute to one of the other [core Wagtail projects](https://github.com/orgs/wagtail/repositories) in GitHub.
-   Contribute to one of the community-maintained packages on [Wagtail Nest](https://github.com/wagtail-nest/).
-   Contribute user-facing documentation (including translations) on the [Wagtail guide](https://guide.wagtail.org/en-latest/contributing/).

### Non-code contributions

-   Star the [wagtail](https://github.com/wagtail/wagtail) project on GitHub
-   Support others with answers to questions on the [Wagtail StackOverflow topic](https://stackoverflow.com/questions/tagged/wagtail) or in Slack `#support`.
-   Write a review of [Wagtail on G2](https://www.g2.com/products/wagtail/reviews).
-   Provide some thoughtful feedback on the [Wagtail discussions](https://github.com/wagtail/wagtail/discussions).
-   Submit (or write) a tutorial or great package to the [This Week in Wagtail newsletter](https://wagtail.org/newsletter/), [Awesome Wagtail](https://github.com/springload/awesome-wagtail) or [](../advanced_topics/third_party_tutorials).

## Developing packages for Wagtail

If you are developing packages for Wagtail, you can add the following [PyPI](https://pypi.org/) classifiers:

-   [`Framework :: Wagtail`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail)
-   [`Framework :: Wagtail :: 1`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+1)
-   [`Framework :: Wagtail :: 2`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+2)
-   [`Framework :: Wagtail :: 3`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+3)
-   [`Framework :: Wagtail :: 4`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+4)
-   [`Framework :: Wagtail :: 5`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+5)
-   [`Framework :: Wagtail :: 6`](https://pypi.org/search/?c=Framework+%3A%3A+Wagtail+%3A%3A+6)

You can also find a curated list of awesome packages, articles, and other cool resources from the Wagtail community at [Awesome Wagtail](https://github.com/springload/awesome-wagtail).

## More information

```{toctree}
:maxdepth: 2

styleguide
general_guidelines
python_guidelines
ui_guidelines
documentation_guidelines
documentation_modes
translations
security
committing
```
