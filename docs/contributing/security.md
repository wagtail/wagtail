# Reporting security issues

```eval_rst
.. note::
   Please report security issues **only** to `security@wagtail.io <mailto:security@wagtail.io>`_.
```

Most normal bugs in Wagtail are reported as [GitHub issues](https://github.com/wagtail/wagtail/issues), but due to the sensitive nature of security issues, we ask that they not be publicly reported in this fashion.

Instead, if you believe you've found something in Wagtail which has security implications, please send a description of the issue via email to <security@wagtail.io>.
Mail sent to that address reaches a subset of the core team, who can forward security issues to other core team members for broader discussion if needed.

Once you've submitted an issue via email, you should receive an acknowledgement from a member of the security team within 48 hours, and depending on the action to be taken, you may receive further followup emails.

If you want to send an encrypted email (optional), the public key ID for <security@wagtail.io> is `0x6ba1e1a86e0f8ce8`, and this public key is available from most commonly-used keyservers.

Django security issues should be reported directly to the Django Project, following [Django\'s security policies](https://docs.djangoproject.com/en/dev/internals/security/) (upon which Wagtail\'s own policies are based).

## Supported versions

At any given time, the Wagtail team provides official security support for several versions of Wagtail:

- The ``main`` development branch, hosted on GitHub, which will become the next release of Wagtail, receives security support.
- The two most recent Wagtail release series receive security support.
  For example, during the development cycle leading to the release of
  Wagtail 2.6, support will be provided for Wagtail 2.5 and Wagtail 2.4. Upon the release of Wagtail 2.6, Wagtail 2.4's security support will end.
- The latest long-term support release will receive security updates.

When new releases are issued for security reasons, the accompanying notice will include a list of affected versions.
This list is comprised solely of supported versions of Wagtail: older versions may also be affected, but we do not investigate to determine that, and will not issue patches or new releases for those versions.

## How Wagtail discloses security issues

Our process for taking a security issue from private discussion to public disclosure involves multiple steps.

There is no fixed period of time by which a confirmed security issue will be resolved as this is dependent on the issue, however it will be a priority of the Wagtail team to issue a security release as soon as possible.

The reporter of the issue will receive notification of the date on which we plan to take the issue public.
On the day of disclosure, we will take the following steps:

1. Apply the relevant patch(es) to Wagtail\'s codebase.
   The commit messages for these patches will indicate that they are for security issues, but will not describe the issue in any detail; instead, they will warn of upcoming disclosure.
2. Issue the relevant release(s), by placing new packages on [the Python Package Index](https://pypi.org/project/wagtail/), tagging the new release(s) in Wagtail\'s GitHub repository and updating Wagtail\'s [release notes](../releases/index).
3. Post a public entry on [Wagtail\'s blog](https://wagtail.io/blog/), describing the issue and its resolution in detail, pointing to the relevant patches and new releases, and crediting the reporter of the issue (if the reporter wishes to be publicly identified).
4. Post a notice to the [Wagtail support forum](https://groups.google.com/d/forum/wagtail) and Twitter feed ([\@WagtailCMS](https://twitter.com/wagtailcms)) that links to the blog post.

If a reported issue is believed to be particularly time-sensitive -- due to a known exploit in the wild, for example -- the time between advance notification and public disclosure may be shortened considerably.
