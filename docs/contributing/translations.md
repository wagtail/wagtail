(contributing_translations)=

# Translations

Wagtail uses [Transifex](https://www.transifex.com/) to translate the content for the admin interface. Our goal is to ensure that Wagtail can be used by those who speak many different languages. Translation of admin content is a great way to contribute without needing to know how to write code.

```{note}
For translations and internationalisation of content made with Wagtail see [](internationalisation).
```

## Translation workflow

Wagtail is localised (translated) using Django's [translation system](django:topics/i18n/translation) and the translations are provided to and managed by [Transifex](https://www.transifex.com/), a web platform that helps organisations coordinate translation projects.

Translations from Transifex are only integrated into the repository at the time of a new release. When a release is close to being ready there will be a RC (Release Candidate) for the upcoming version and the translations will be exported to Transifex.

During this RC period, usually around two weeks, there will be a chance for all the translators to update and add new translations. We will also notify the `#translators` channel in the Wagtail Slack group at this time.

These new translations are imported into Wagtail for any subsequent RC and the final release. If translations reach a threshold of about 80%, languages are added to the default list of languages users can choose from.

### How to help out with translations

-   Join the Wagtail community on [Slack](https://wagtail.org/slack/)
-   Search through the channels to join the `#translator` channel and introduce yourself
-   Go to [Transifex](https://www.transifex.com/)
-   Click on start for free
-   Fill in your Username, Email and Password
-   Agree to the terms and conditions
-   Click on free trial or join an existing organisation
-   Join [Wagtail](https://www.transifex.com/torchbox/wagtail/dashboard/) and see the list of languages on the dashboard
-   Request access to become a member of the language team you want to work with on Slack (mention your Transifex username)
-   A view resources button appears when you hover over the ready to use part on the right side of the page
-   Click on the button to get access to the resources available
-   This takes you to the language section
-   This page has a translation panel on the right and a list of strings to be translated on the left
-   To translate a project, select it and enter your translation in the translation panel
-   Save the translation using the translation button on the panel

## Additional resources

-   [](django:topics/i18n/translation)
-   A screen-share [Wagtail Space US 2020 Lightning Talk](https://www.youtube.com/watch?v=sLI_AuOMUQw&t=17s) that walks through using Transifex step-by-step
-   [Core development instructions for syncing Wagtail translations with Transifex](https://github.com/wagtail/wagtail/wiki/Managing-Wagtail-translations)
