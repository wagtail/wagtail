<h1 align="center">
	<img width="343" src="https://cdn.rawgit.com/wagtail/wagtail/master/.github/wagtail.svg" alt="Wagtail">
	<br>
	<br>
</h1>

Wagtail is an open source content management system built on Django, with a strong community and commercial support. It's focused on user experience, and offers precise control for designers and developers.

![Wagtail screenshot](https://cdn.rawgit.com/wagtail/wagtail/master/.github/wagtail-screenshot-with-browser.png)

### Features

* A fast, attractive interface for authors
* Complete control over front-end design and structure
* Scales to millions of pages and thousands of editors
* Fast out of the box, cache-friendly when you need it
* Content API for 'headless' sites with de-coupled front-end
* Runs on a Raspberry Pi or a multi-datacenter cloud platform 
* StreamField encourages flexible content without compromising structure
* Powerful, integrated search, using Elasticsearch or PostgreSQL
* Excellent support for images and embedded content
* Multi-site and multi-language ready
* Embraces and extends Django

Find out more at [wagtail.io](https://wagtail.io/).

### Getting started

Wagtail works with Python 3, on any platform.

```
    pip install wagtail
    wagtail start mysite
    cd mysite
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
```

For detailed installation and setup docs, see [docs.wagtail.io](http://docs.wagtail.io/).

### Who’s using it?

Wagtail is used by NASA, Google, Oxfam, the NHS, Mozilla, MIT, the Red Cross, Salesforce, NBC, BMW, and the US and UK governments. Add your own Wagtail site to [madewithwagtail.org](http://madewithwagtail.org).

### Documentation

[docs.wagtail.io](http://docs.wagtail.io/) is the full reference for Wagtail, and includes guides for developers, designers and editors, alongside release notes and our roadmap.

### Compatibility

Wagtail supports:

* Django 1.11.x, 2.0.x and 2.1.x
* Python 3.4, 3.5 and 3.6
* PostgreSQL, MySQL and SQLite as database backends

Previous versions of Wagtail (1.13 and earlier) additionally supported Python 2.7.

---

### Community Support

There is an active community of Wagtail users and developers responding to questions on [Stack Overflow](http://stackoverflow.com/questions/tagged/wagtail). When posting questions, please read Stack Overflow's advice on [how to ask questions](http://stackoverflow.com/help/how-to-ask) and remember to tag your question "wagtail".

For topics and discussions that do not fit Stack Overflow's question and answer format, we have a [Slack workspace](https://github.com/wagtail/wagtail/wiki/Slack) and a [Wagtail Support mailing list](https://groups.google.com/forum/#!forum/wagtail). Please respect the time and effort of volunteers by not asking the same question in multiple places.

We maintain a curated list of third party packages, articles and other resources at [Awesome Wagtail](https://github.com/springload/awesome-wagtail).

### Commercial Support

Wagtail is sponsored by [Torchbox](https://torchbox.com/). If you need help implementing or hosting Wagtail, please contact us: hello@torchbox.com. See also [madewithwagtail.org/developers/](https://madewithwagtail.org/developers/) for expert Wagtail developers around the world.

### Contributing

If you're a Python or Django developer, fork the repo and get stuck in! We run a separate group for developers of Wagtail itself at https://groups.google.com/forum/#!forum/wagtail-developers (please note that this is not for support requests).

You might like to start by reviewing the [contributing guidelines](http://docs.wagtail.io/en/latest/contributing/index.html) and checking issues with the [good first issue](https://github.com/wagtail/wagtail/labels/good%20first%20issue) label.

We also welcome translations for Wagtail's interface. Translation work should be submitted through [Transifex](https://www.transifex.com/projects/p/wagtail/).

### Thanks

We thank [BrowserStack](https://www.browserstack.com/), who provide the project with free access to their live web-based browser testing tool, and automated Selenium cloud testing.

[![Browserstack](https://cdn.rawgit.com/wagtail/wagtail/master/.github/browserstack-logo.svg)](https://www.browserstack.com/)

[![Build Status](https://api.travis-ci.org/wagtail/wagtail.svg?branch=master)](https://travis-ci.org/wagtail/wagtail)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Version](https://img.shields.io/pypi/v/wagtail.svg)](https://pypi.python.org/pypi/wagtail/) 
[![Coverage](http://codecov.io/github/wagtail/wagtail/coverage.svg?branch=master)](http://codecov.io/github/wagtail/wagtail?branch=master)
[![Slack](https://wagtail-slack.now.sh/badge.svg)](https://wagtail-slack.now.sh)