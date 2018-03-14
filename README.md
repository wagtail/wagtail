![Wagtail](https://releases.wagtail.io/wagtail-github-header.png?x)

Wagtail is a content management system built on Django. It's focused on user experience, and offers precise control for designers and developers. 

[![Build Status](https://api.travis-ci.org/wagtail/wagtail.svg?branch=master)](https://travis-ci.org/wagtail/wagtail) 
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Version](https://img.shields.io/pypi/v/wagtail.svg)](https://pypi.python.org/pypi/wagtail/) 
[![Coverage](http://codecov.io/github/wagtail/wagtail/coverage.svg?branch=master)](http://codecov.io/github/wagtail/wagtail?branch=master)

### Features

* A fast, attractive interface for authors and editors
* Complete control over design with standard Django templates
* Configure content types through standard Django models
* Fast out of the box. Cache-friendly if you need it
* Tightly integrated search
* Strong document and image management
* Wide support for embedded content
* Straightforward integration with existing Django apps
* Simple, configurable permissions
* An extensible [form builder](http://docs.wagtail.io/en/latest/reference/contrib/forms/index.html)
* Multi-site and multi-language support

Find out more at https://wagtail.io

### Getting started

Wagtail works with Python 3.4 and up, on any platform.

```
    pip install wagtail
    wagtail start mysite
    cd mysite
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
```

For detailed installation and setup docs, see [docs.wagtail.io](http://docs.wagtail.io/)

### Who's using it?

Wagtail is used by NASA, Google, Oxfam, the NHS, Mozilla, MIT, the Red Cross, Salesforce, NBC, BMW, the US and UK governments. Add your own Wagtail site to [madewithwagtail.org](http://madewithwagtail.org).

### Documentation

[docs.wagtail.io](http://docs.wagtail.io/) is the full reference for Wagtail, and includes guides for developers, designers and editors, alongside release notes and our roadmap.

### Community Support

There is an active community of Wagtail users and developers responding to questions on [Stack Overflow](http://stackoverflow.com/questions/tagged/wagtail). When posting questions, please read Stack Overflow's advice on [how to ask questions](http://stackoverflow.com/help/how-to-ask) and remember to tag your question "wagtail".

For topics and discussions that do not fit Stack Overflow's question-and-answer format, there is also a [Wagtail Support mailing list](https://groups.google.com/forum/#!forum/wagtail) and a [Slack workspace](https://github.com/wagtail/wagtail/wiki/Slack).

### Commercial Support

Wagtail is sponsored by [Torchbox](https://torchbox.com/). If you need help implementing or hosting Wagtail, please contact us: hello@torchbox.com.

### Thanks

We thank [BrowserStack](https://www.browserstack.com/), who provide the project with free access to their live web-based browser testing tool, and automated Selenium cloud testing.

[![Browserstack](https://cdn.rawgit.com/wagtail/wagtail/master/.github/browserstack-logo.svg)](https://www.browserstack.com/)

### Compatibility
Wagtail supports Django 1.11.x and 2.0 on Python 3.4, 3.5 and 3.6. Supported database backends are PostgreSQL, MySQL and SQLite.

### Contributing
If you're a Python or Django developer, fork the repo and get stuck in! We run a separate group for developers of Wagtail itself at https://groups.google.com/forum/#!forum/wagtail-developers (please note that this is not for support requests).

You might like to start by reviewing the [contributing guidelines](http://docs.wagtail.io/en/latest/contributing/index.html) and checking issues with the [good first issue](https://github.com/wagtail/wagtail/labels/good%20first%20issue) label.

We also welcome translations for Wagtail's interface. Translation work should be submitted through [Transifex](https://www.transifex.com/projects/p/wagtail/).
