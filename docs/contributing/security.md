# Reporting security issues

```{warning}
Ensure you are viewing our [latest security policy](https://docs.wagtail.org/en/latest/contributing/security.html).
```

```{note}
Please report security issues **only** to [security@wagtail.org](mailto:security@wagtail.org).
```

Most normal bugs in Wagtail are reported as [GitHub issues](https://github.com/wagtail/wagtail/issues), but due to the sensitive nature of security issues, we ask that they not be publicly reported in this fashion.

Instead, if you believe you've found something in Wagtail which has security implications, please send a description of the issue via email to <security@wagtail.org>.
Mail sent to that address reaches a subset of the core team, who can forward security issues to other core team members for broader discussion if needed.

Once you've submitted an issue via email, you should receive an acknowledgment from a member of the security team within 48 hours, and depending on the action to be taken, you may receive further followup emails.

If you want to send an encrypted email (optional), the public key ID for <security@wagtail.org> is `0xbed227b4daf93ff9`, and this public key is available from most commonly-used keyservers.

This information can also be found in our [security.txt](https://wagtail.org/.well-known/security.txt).

Django security issues should be reported directly to the Django Project, following [Django's security policies](inv:django#internals/security) (upon which Wagtail's own policies are based).

## Supported versions

At any given time, the Wagtail team provides official security support for several versions of Wagtail:

-   The `main` development branch, hosted on GitHub, which will become the next release of Wagtail, receives security support.
-   The two most recent Wagtail release series receive security support.
    For example, during the development cycle leading to the release of
    Wagtail 2.6, support will be provided for Wagtail 2.5 and Wagtail 2.4. Upon the release of Wagtail 2.6, Wagtail 2.4's security support will end.
-   The latest long-term support release will receive security updates.

When new releases are issued for security reasons, the accompanying notice will include a list of affected versions.
This list is comprised solely of supported versions of Wagtail: older versions may also be affected, but we do not investigate to determine that, and will not issue patches or new releases for those versions.

## Bug Bounties

Wagtail does not have a "Bug Bounty" program. Whilst we appreciate and accept reports from anyone, and will gladly give credit to you and/or your organisation, we aren't able to "reward" you for reporting the vulnerability.

["Beg Bounties"](https://www.troyhunt.com/beg-bounties/) are ever increasing among security researchers, and it's not something we condone or support.

## CVE IDs

When published, vulnerabilities in Wagtail are given a CVE (Common Vulnerability and Exposures) ID (eg `CVE-2020-15118`). The Wagtail project uses GitHub's [Security Advisories](https://github.com/wagtail/wagtail/security/advisories) to record vulnerabilities, request CVE IDs and track both upcoming and historical vulnerabilities. GitHub therefore acts as Wagtail's CNA (CVE Numbering Authority).

If you have found a vulnerability in Wagtail, please report it using the information above - **do not** request a CVE ID. CVEs will be requested by the security team as part of the resolution process and correctly populated with details and credit where necessary, and **must not** be requested otherwise.

Any CVEs issued for vulnerabilities not discussed with the Wagtail security team, or otherwise issued or requested erroneously will be disputed and may be later rejected.

## How Wagtail discloses security issues

Our process for taking a security issue from private discussion to public disclosure involves multiple steps.

There is no fixed period of time by which a confirmed security issue will be resolved as this is dependent on the issue, however it will be a priority of the Wagtail team to issue a security release as soon as possible.

The reporter of the issue will receive notification of the date on which we plan to take the issue public.
On the day of disclosure, we will take the following steps:

1. Apply the relevant patch(es) to Wagtail's codebase.
   The commit messages for these patches will indicate that they are for security issues, but will not describe the issue in any detail; instead, they will warn of upcoming disclosure.
2. Issue the relevant release(s), by placing new packages on [the Python Package Index](https://pypi.org/project/wagtail/), tagging the new release(s) in Wagtail's GitHub repository and updating Wagtail's [release notes](../releases/index).
3. Publish a [security advisory](https://github.com/wagtail/wagtail/security/advisories?state=published) on Wagtail's GitHub repository. This describes the issue and its resolution in detail, pointing to the relevant patches and new releases, and crediting the reporter of the issue (if the reporter wishes to be publicly identified)
4. Post a notice to the [Wagtail discussion board](https://github.com/wagtail/wagtail/discussions), [Slack workspace](https://wagtail.org/slack/) and X feed ([\@WagtailCMS](https://x.com/wagtailcms)) that links to the security advisory.

If a reported issue is believed to be particularly time-sensitive -- due to a known exploit in the wild, for example -- the time between advance notification and public disclosure may be shortened considerably.

## CSV export security considerations

In various places Wagtail provides the option to export data in CSV format, and several reporters have raised the possibility of a malicious user inserting data that will be interpreted as a formula when loaded into a spreadsheet package such as Microsoft Excel. We do not consider this to be a security vulnerability in Wagtail. CSV as defined by [RFC 4180](https://datatracker.ietf.org/doc/html/rfc4180) is purely a data format, and makes no assertions about how that data is to be interpreted; the decision made by certain software to treat some strings as executable code has no basis in the specification. As such, Wagtail cannot be responsible for the data it generates being loaded into a software package that interprets it insecurely, any more than it would be responsible for its data being loaded into a missile control system. This is consistent with [the Google security team's position](https://sites.google.com/site/bughunteruniversity/nonvuln/csv-excel-formula-injection).

Since the CSV format has no concept of formulae or macros, there is also no agreed-upon convention for escaping data to prevent it from being interpreted in that way; commonly-suggested approaches such as prefixing the field with a quote character would corrupt legitimate data (such as phone numbers beginning with '+') when interpreted by software correctly following the CSV specification.

Wagtail's data exports default to XLSX, which can be loaded into spreadsheet software without any such issues. This minimizes the risk of a user handling CSV files insecurely, as they would have to explicitly choose CSV over the more familiar XLSX format.
