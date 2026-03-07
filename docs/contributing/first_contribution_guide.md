# Your first contribution

```{contents}
---
local:
depth: 1
---
```

This page has a step by step guide for how to get started making contributions to Wagtail. It is recommended for developers getting started with open source generally or with only a small amount of experience writing code for shared teams.

This is a long guide - do not worry about following all the steps in one go or doing them perfectly. There are lots of people around in the community to help, but if you can take the time to read and understand yourself you will be a much stronger developer.

Each section has an introduction with an overview and a checklist that can be copied and pasted for you to check through one by one. Get ready to read, there is a lot of reading ahead.

```{note}
Avoid 'claiming' any issues before completing Steps 0-6. This helps you not over-promise what you can contribute and helps the community support you when you are actually ready to contribute.
Do not worry about issues 'running out' - software development is an endless fractal, there is always more to help with.
```

## Guide

### 0. Understand your motivations

Before you start contributing to Wagtail, take a moment to think about why you want to do it. If your only goal is to add a "first contribution" to your resume (or if you're just looking for a quick win) you might be better off doing a boot-camp or an online tutorial.

Contributing to open source projects takes time and effort, but it can also help you become a better developer and learn new skills. However, it's important to know that it might be harder and slower than following a training course. That said, contributing to open source is worth it if you're willing to take the time to do things well.

One thing to keep in mind is that "scratching your own itch" can be a great motivator for contributing to open source. If you're interested in the CMS space or the programming languages used in this project, you'll be more likely to stick with it over the long term.

### 1. Understanding what Wagtail is

Before you start contributing to Wagtail, it's important to understand what it is and how it works. Wagtail is a content management system (CMS) used for building websites. Unlike other CMSs, it requires some development time to build up the models and supporting code to use as a CMS. Additionally, Wagtail is built on top of another framework called Django, which is a Python web framework. This might be confusing at first, but it provides a powerful way to create custom systems for developers to build with.

To get started, we recommend reading [the Zen of Wagtail](../getting_started/the_zen_of_wagtail), which provides a good introduction to the project. You might also want to read the [Django overview](inv:django#intro/overview) to understand what Django provides. To get a sense of how Wagtail fits into the CMS landscape, you can search online for articles that compare WordPress to Wagtail or list the top open source CMSs. Finally, reading some of the [Wagtail Guide](https://guide.wagtail.org/) will give you a better understanding of how the CMS works for everyday users.

```{note}
Below is a checklist. There are many like these you can copy for yourself as you progress through this guide.
```

```markdown
-   [ ] Read the Zen of Wagtail.
-   [ ] Read the Django Overview.
-   [ ] Search online for one or two articles that 'compare Wordpress to Wagtail' or 'top ten open source CMS' and read about the CMS landscape.
-   [ ] Read some of the Wagtail Guide.
```

### 2. Joining the community

Make an account on [Wagtail Slack](https://github.com/wagtail/wagtail/wiki/Slack) server, this is the way many of the community interact day to day. Introduce yourself on `#new-contributors` and join some of the other channels, remember to keep your intro short and be nice to others. After this, join [GitHub](https://github.com/) and set up your profile. It's really helpful to the community if your name can be added to your profiles in both communities and an image. It does not have to be your public name or a real image if you want to keep that private but please avoid it staying as the 'default avatar'.

You may also want to join StackOverflow and [follow the Wagtail tag](https://stackoverflow.com/questions/tagged/wagtail), this way you can upvote great answers to questions you have or maybe consider contributing answers yourself. Before you dive in, take a moment to review the [community guidelines](https://github.com/wagtail/wagtail/blob/main/CODE_OF_CONDUCT.md) to get a grasp on the expectations for participation.

#### Checklist

```markdown
-   [ ] Read the community guidelines.
-   [ ] Join GitHub.
-   [ ] Add your preferred name and image to your GitHub profile.
-   [ ] Join Slack.
-   [ ] Add your preferred name, timezone and image to your Slack profile.
-   [ ] Introduce yourself in `#new-contributors` in Slack.
-   [ ] Join the `#support` channel in Slack.
-   [ ] _Optional_ Join StackOverflow.
```

### 3. Before contributing code

Firstly, it is important to be able to understand how to **build with** Wagtail before you can understand how to contribute **to** Wagtail. Take the time to do the full [Wagtail getting started tutorial](../getting_started/index) without focusing yet on how to contribute code but instead on how to use Wagtail to build your own basic demo website. This will require you to have Python and other dependencies installed on your machine and may not be easy the first time, but keep at it and ask questions if you get stuck.

Remember that there are many other ways to contribute, such as answering questions in StackOverflow or `#support`, contributing to one of the [other packages](https://github.com/wagtail/) or even the [Wagtail user guide](https://guide.wagtail.org/en-latest/contributing/). Sometimes, it's best to get started with a non-code contribution to get a feel for Wagtail's code or the CMS interface.

Issue tracking, reading and triage is a critical part of contributing code and it is recommended that you read the [issue tracking guide](issue_tracking) in full. This will help you understand how to find issues to work on and how to support the team with triaging issues.

```{note}
Take the time to **read** the issue and links before adding new comments or questions. Remember, it's not time to 'claim' any issues yet either.
```

#### Checklist

```
- [ ] Do the Wagtail tutorial.
- [ ] Look at the Wagtail organization on GitHub, take note of any interesting projects.
- [ ] Read through the Issue Tracking section in the docs.
- [ ] Give a go at a non-code contribution.
```

### 4. Setting up your development environment

<!--
Important: This section should not go too deep into development setup. Instead we should solidify the content on the development page.
-->

Many contribution sections gloss over the mammoth task that can be a single line in the documentation similar to “fork the code and get it running locally”. This, on its own, can be a daunting task if you are just getting started. This is why it's best to have done the Wagtail tutorial before this step so you have run into and hopefully solved many of the normal developer environment issues.

First, create a fork of Wagtail on your GitHub account (see below for more details).

```{note}
Do not try to move past this step until you have a working `bakerydemo` code locally and a clone of the Wagtail repo that you can edit. When editing the Wagtail core code (both HTML and JavaScript) you should be able to refresh the site running locally and see the changes.
```

Read (in full) the [Development guide](developing_for_wagtail). This will walk you through how to get your code running locally so you can contribute. It's strongly recommended to use the Vagrant or Docker setups, especially if you are working on Windows.

```{note}
When developing, it's recommended that you always read the `latest` version of the docs. Not the `stable` version. This is because it will better reflect what's on the `main` code branch.
```

#### Checklist

```
- [ ] Install `git` (if not on your machine).
- [ ] Install a code editor/IDE (we recommend VSCode).
- [ ] Install the dependencies set out in the development guide.
- [ ] Follow the development guide.
- [ ] Make a change to the `wagtail/admin/templates/wagtailadmin/home.html` template file and confirm you can see the changes on the Wagtail dashboard (home) page.
- [ ] Add a `console.log` statement to `client/src/entrypoints/admin/wagtailadmin.js` and confirm you can see the logging in the browser.
```

#### Aside: Understanding Git and GitHub

`git` is the version control tool, it is something you install on your device and runs usually in the command line (terminal) or via some GUI application.

GitHub & GitLab are two prominent websites that provide a web user interface for repositories using `git`, Wagtail uses GitHub.

Mozilla has a great guide that helps to explain [Git and GitHub](https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/GitHub).

How to clone a remote repository and what that actually even means:

-   On GitHub, you will not be allowed to directly create branches or changes in a repository (project) that you do not have access to.
-   However, you can make a copy (clone) of this repository using your own account, this clone will have all the branches and history that the original repository had.
-   This is also called ‘fork’ in some cases, as your repository will be a branch of its own that forks the original repository.
-   See the [GitHub docs explain forking](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).
-   See [Atlassian’s docs on git clone](https://www.atlassian.com/git/tutorials/setting-up-a-repository/git-clone) for more details.

### 5. Finding an issue

Hopefully, at this point, you have a good sense of the purpose of the project and are still keen to contribute.

Once you have the code forked and running locally, you will probably want to start looking for what to contribute.

Finding something to contribute is not always easy, especially if you are new to the project. Once you have a few candidate issues to investigate, be sure to read the entire issue description, all comments and all linked issues or pull requests. You may often find that someone else has started or finished the issue. Sometimes there are clarifications in the comments about how to approach the problem or whether the problem is even something worth solving.

If an issue has a pull request linked and not yet merged read that pull request and the discussion on it. Maybe the previous contributor got stuck or lost momentum, in which case you could pick up where they left off (assuming it's been enough time). If you have an idea about how to solve a problem, just add a comment with a suggestion, we should all aim to help each other out.

If the issue is labelled [`good-first-issue`](https://github.com/wagtail/wagtail/labels/good%20first%20issue), that usually means it is smaller and good for first time contributors. There are no problems with finding other issues to contribute to, have a search around and see what you can help with.

Finally, before 'claiming' check you can do the following;

#### Checklist (for a candidate issue)

```markdown
-   [ ] Confirm that there is not someone actively working on it (no recent PR or comments in the last ~2 months).
-   [ ] Ensure you can reproduce the problem/scenario in your local version of Wagtail.
-   [ ] Ensure that you feel confident to write a unit test (if it's a code change) to validate that the solution **is** implemented.
```

### 6. Contributing a solution

**Important:** If an issue is not assigned to anyone and doesn’t already have a pull request, feel free to work on it, **no need to ask "please assign me this issue"**. We only use GitHub's issue assignment feature to assign certain issues to members of the Wagtail core team.

If you feel ready to contribute a solution, now is a good time to add a comment to the issue describing your intention to do so, to prevent duplicating efforts. Instead of asking "please assign me this issue", write something similar to the following:

```{note}
I have been able to reproduce this problem/scenario. I am planning to work on this, my rough solution is (...explain).
```

If it's just a documentation request, you may refine this comment to explain where you plan to add the section in the documentation.

#### Create a fresh branch for your contributions

Before writing any code, take a moment to get your `git` hat on. When you clone the project locally, you will be checked out at the `main` branch. This branch is not suitable for you to make your changes on. It is meant to be the branch that tracks the core development of the project.

Instead, take a moment to create a [new branch](https://www.atlassian.com/git/tutorials/using-branches). You can use the command line or install one of the many great git GUI tools. Don't listen to anyone that says you're not doing it right unless you use the command line. Reduce the things you need to learn today and focus on the `git` command line interface later. If you have a Mac, I recommend [Fork](https://git-fork.com/), otherwise, the [GitHub GUI](https://desktop.github.com/) is good enough.

This new branch name should have some context as to what you are fixing and if possible the issue number being fixed. For example `git checkout -b 'feature/1234-add-unit-tests-for-inline-panel'`. This branch name uses `/` to represent a folder and also has the issue number `1234`, finally, it uses `lower-kebab-case` with a short description of the issue.

```{note}
You may find that your editor has some handy Git tooling and will often be able to tell you what branch you are on or whether you have any changes staged. For example, see [VS Code's support for Git](https://code.visualstudio.com/docs/sourcecontrol/overview).
```

#### Keep the changes focused

As a developer, it is easy to get distracted, maybe a typo here or white space that does not feel 'right' there. Sometimes, even our editor gets distracted and starts adding line breaks at the end of files as we save or it formats code without our consent due to configuration from a different project.

These added changes that are not the primary goal or not strictly required by the project's set-up are noise. This noise makes it harder to review the pull request and also can create confusion for future developers that see these commits and wonder how it relates to the bug that was fixed.

When you go to stage changes, only stage the parts you need or at least review the changes and 'undo' them before you save the commits.

If you do find a different problem (maybe a typo in the docs for example) this is what branches are for. Save your commits, create a new branch off master `fix/fix-documentation-typo` and then save that change to that branch. Now you have a small change, one that is easy to merge, which you can prepare a pull request for.

Keep your changes focused on the goal, do not add overhead to the reviewer or to yourself by changing things that do not need it (yet).

```{note}
It's OK to make changes in a 'messy' way locally, with lots of commits that maybe include things that are not needed. However, be sure to take some time to review your commits and clean up anything that is not required before you do your pull request.
```

#### Write unit tests

We are getting close to having a pull request, but the next critical step is unit tests. It's common to find that adding tests for code you wrote will take 5-10x longer than the actual bug fix. Often, if the use case is right, it is better to write the tests first and get them running (but failing) before you fix the problem.

Finding how and where to write the unit tests can be hard in a new project, but hopefully, the project's development docs contain the clues you need to get started. Read through the [dedicated testing section](testing) in the development documentation.

If you fix a bug or introduce a new feature, you want to ensure that fix is long-lived and does not break again. You also want to help yourself by thinking through edge cases or potential problems. Testing helps with this. While regressions do happen, they are less likely to happen when code is tested.

Many projects will not even review a pull request without unit tests. Often, fixing a bug is not hard, ensuring the fix is the 'real' fix and that it does not break again is the hard part. Take the time to do the harder thing. It will help you grow as a developer and help your contributions make a longer lasting difference.

```{note}
A pull request that just adds unit tests to some core functionality that does not yet have tests is a great way to contribute, it helps you learn about the code and makes the project more reliable.
```

#### Checklist

```
- [ ] After feeling confident about a solution, add a comment to the issue.
- [ ] Create a new branch off `main` to track your work separate from the main branch.
- [ ] Keep the changes focused towards your goal, asking questions on the issue if direction is needed.
- [ ] Write unit tests.
```

### 7. Submitting a pull request

A pull request that has the title 'fixes issue' is unhelpful at best, and spammy at worst. Take a few moments to think about how to give your change a title. Communicate (in a few words) the problem solved or feature added or bug fixed. Instead of 'Fixes 10423', use words and write a title 'Fixes documentation dark mode refresh issue'. No one in a project knows that issue `10423` is that one about the documentation dark mode refresh issue.

Please try to add a proper title when you create the pull request. This will ensure that any notifications that go out to the team have a suitable title from the start.

```{note}
Remember you can make a **draft** pull request in both GitHub and GitLab. This is a way to run the CI steps but in a way that indicates you are not ready for a review yet.
```

Referencing the issue being fixed within the pull request description is just as important as a good title. A pull request without a description is very difficult to review. Adding a note similar to `fixes #1234` in your description message will let GitHub know that the change is for that issue. Add some context and some steps to reproduce the issue or scenario.

If the change is visual it's strongly recommended to add before and after screenshots. This helps you confirm the change has worked and also helps reviewers understand the change made.

It is often good to write yourself a checklist for any pull request and fill in the gaps. **Remember that the pull request template is there for a reason so please use that checklist also.**

#### Checklist (for a pull request)

```markdown
-   [ ] Small description of the solution, one sentence.
-   [ ] Link to issue/s that should be resolved if this pull request gets merged.
-   [ ] Questions or assumptions, maybe you made an assumption we no longer support IE11 with your CSS change, if it's not in the docs - write the assumption down.
-   [ ] Details - additional details, context or links that help the reviewer understand the pull request.
-   [ ] Screenshots - added before and after the change has been applied.
-   [ ] Browser and accessibility checks done, or not done. Added to the description.
```

#### 7a. Review & fix the CI failures

Once you have created your pull request, there will often be a series of [build/check/CI](https://about.gitlab.com/topics/ci-cd/) steps that run.

These steps are normally all required to pass before the pull request can be merged. CI is a broad term but usually, the testing and linting will run on the code you have proposed to change. Linting is a tricky one because sometimes the things that are flagged seem trivial, but they are important for code consistency. Re-read the development instructions and see how you can run the linting locally to avoid frustrating back & forth with small linting fixes.

Testing is a bit more complex. Maybe all the tests can be run locally or maybe the CI will run tests on multiple versions of a project or language. Do your best to run all the tests locally, but there may still be issues on the CI when you do. That is OK, and normally you can solve these issues one by one.

The most important thing is to not just ignore CI failures. Read through each error report and try to work out the problem and provide a fix. Ignoring these will likely lead to pull requests that do not get reviewed because they do not get the basics right.

```{note}
GitHub will not run the CI automatically for new contributors in some projects. This is an intentional security feature and a core contributor will need to approve your initial CI run.
```

#### 7b. Push to the same branch with fixes and do not open a new pull request

Finally, after you have fixed the failing linting and tests locally, you will want to push those changes to your remote branch. You do not need to open a new pull request. This creates more noise and confusion. Instead, push your changes up to your branch, and the CI will run automatically on those changes.

You can add a comment if you want to the pull request that you have updated, but often this is not really needed.

**Avoid opening multiple pull requests for the same fix.** Doing that means all the comments and discussion from the previous pull request will get lost and reviewers will have trouble finding them.

### 8. Next steps

When you take time to contribute out of your own personal time, or even that from your paid employer, it can be very frustrating when a pull request does not get reviewed. It is best to temper your expectations with this process and remember that many people on the other side of this are also volunteers or have limited time to prioritize.

It is best to celebrate your accomplishment at this point even if your pull request never gets merged. It's good to balance that with an eagerness about getting your amazing fix in place to help people who use the project. Balancing this tension is hard, but the unhelpful thing to do is give up and never contribute or decide that you won’t respond to feedback because it came too late.

Remember that it is OK to move on and try something else. Try a different issue or project or area of the code. Don’t just sit waiting for a response on the one thing you did before looking at other challenges.

#### Responding to a review

Almost every pull request (PR) (except for the smallest changes) will have some form of feedback. This will usually come in the form of a review and a request for changes. At this point your PR will be flagged as 'needs work', 'needs tests' or in some cases 'needs design decision'. Take the time to read all the feedback and try to resolve or respond to comments if you have questions.

```{warning}
Avoid closing the PR only to create a new one, instead keep it open and push your changes/fixes to the same branch. Unless directed to make the PR smaller, keep the same one open and work through items one by one.
```

Once you feel that you have answered all the concerns, just add a comment (it does not need to be directed at the reviewer) that this is ready for another review.

#### Once merged in

Well done! It's time to party! Thank you for taking the time to contribute to Wagtail and making the project better for thousands of users.

## Common questions

### How can I start contributing?

-   Ideally, read this guide in full, otherwise see some quick start tips.
-   Start simple - pick something small first. The [good first issue](https://github.com/wagtail/wagtail/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22) label is a good place to look.
-   Read the entire issue, all comments (links) and related issues.
-   Someone may have started work (that work may have stalled).
-   Check if assigned, we do not usually use that unless assigned to someone within the core team.

If you have done all of that and think you can give it a go, add a comment with something like 'I will give this a go'. No need to ask for permission.

### Do I need to ask for permission to work on an issue?

**No.** However, check if there is an existing pull request (PR). If there is nothing, you can optionally add a comment mentioning that you're starting work on it.

### What should I include in my pull request (PR)

0. The fix or feature you are working on
1. Tests
2. Linted code (we make use of [pre-commit](https://pre-commit.com/). You can run all formatting with `make format`)
3. Updated documentation where relevant (such as when adding a new feature)

### What if I fix multiple issues in the same pull request (PR)

It is best to avoid fixing more than one issue in a single pull request, unless you are a core contributor or there is a clear plan that involves fixing multiple things at once. Even then, it is usually a bad idea as it makes it harder for your pull request to be reviewed and it may never get merged as it's too complex. This is especially true for completely unrelated issues such as a documentation fix for translators and a bug fix for StreamField. It is always best to create two branches and then two separate pull requests.

### When do I need to write unit tests for a pull request (PR)?

Unless you are updating the documentation or only making visual style changes, your pull request should contain tests.

If you are new to writing tests in Django, start by reading the [Django documentation on testing](inv:django#topics/testing/overview). Re-read the [Wagtail documentation notes on testing](testing) and have a look at [existing tests](https://cs.github.com/?scopeName=All+repos&scope=&q=repo%3Awagtail%2Fwagtail+path%3A**%2Ftests%2F**).

Note that the JavaScript testing is not as robust as the Python testing, if possible at least attempt to add some basic JS tests to new behavior.

### Where can I get help with my pull request (PR)?

The `#new-contributors` channel in [Slack](https://github.com/wagtail/wagtail/wiki/Slack) is the best place to get started with support for contributing code, especially for help with the process of setting up a dev environment and creating a PR.

There is also the more recently created `#development` channel for advice on understanding and getting around the Wagtail code-base specifically. Finally, if you have a general problem with understanding how to do something in Wagtail itself or with a specific feature, then `#support` can be used.

### What if there is already an open pull request (PR)?

Be sure to always read the issue in full and review all links, sometimes there may already be an open pull request for the same issue. To avoid duplicating efforts it would be best to see if that pull request is close to ready and then move on to something else. Alternatively, if it has been a long enough amount of time, you may want to pick up the code and build on it to get it finished or ask if they need help.

### Can I just use Gitpod to develop?

While Gitpod is great for some small scale pull requests, it will not be a suitable tool for complex contributions and it's best to take the time to set up a fully functional development environment so you can manage branches and ongoing commits to one branch.

Here are some links for using Gitpod with the Wagtail packages:

-   [Bakerydemo Gitpod instructions](https://github.com/wagtail/bakerydemo#setup-with-gitpod)
-   [Wagtail Gitpod – Wagtail development setup in one click](https://wagtail.org/blog/gitpod/)

### Can I use Windows to develop?

While a lot of our documentation works best on Linux or MacOS, we do have some guidance for [development on Windows](development_on_windows).

You can also go through this [Windows step by step guide to getting bakerydemo running with local Wagtail](https://juliet.hashnode.dev/a-step-by-step-guide-for-manually-setting-up-bakery-demo-with-wagtail).

### How can I be assigned an issue to contribute to?

We only use GitHub's issue assignment feature for members of the Wagtail core team when tasks are being planned as part of core roadmap features or when being used for a specific internship program. If an issue is not assigned to anyone, feel free to work on it, there is no need to ask to be assigned the issue.

Instead, review the issue, understand it and if you feel you can contribute you can just raise a pull request, or add a comment that you are taking a look at this. There are no strict claiming or reserving rules in place, anyone is free to work on any issue, but try to avoid double effort if someone has already got a pull request underway.

## Helpful links

-   [Django's contributor guide](inv:django#internals/contributing/index) is a helpful resource for contributors, even those not contributing to Wagtail.
-   [MDN's open source etiquette](https://developer.mozilla.org/en-US/docs/MDN/Community/Open_source_etiquette) is a great guideline for how to be a great contributor.
-   [Learning Git Branching](https://learngitbranching.js.org/) a solid interactive guide to understand how git branching works.
-   [Hacktoberfest](https://hacktoberfest.com/) every October, join in the fun and submit pull requests.
-   [21 Pull Requests](https://24pullrequests.com/) a December community effort to contribute to open source.

### Inspiration for this content

Some great further reading also

-   [5 simple ways anyone can contribute to Wagtail](https://wagtail.org/blog/5-simple-ways-anyone-can-contribute-to-wagtail/)
-   [Ten tasty ingredients for a delicious pull request](https://wagtail.org/blog/ten-tasty-ingredients-for-a-delicious-pull-request/)
-   [Preparing a Gourmet Pull Request](https://johnfraney.ca/blog/preparing-a-gourmet-pull-request/)
-   [Zulip's contributor guide](https://zulip.readthedocs.io/en/latest/contributing/contributing.html)
-   [Documentation for absolute beginners to software development (discussion)](https://github.com/wagtail/wagtail/discussions/9557)
-   [New contributor FAQ](https://github.com/wagtail/wagtail/wiki/New-contributor-FAQ)
