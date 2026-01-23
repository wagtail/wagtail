(deployment_guide)=

# Deployment & hosting

```{toctree}
---
maxdepth: 2
hidden: True
---
flyio
under_the_hood
```

Once you've built your Wagtail site, it's time to release it upon the rest of the internet.

Wagtail is built on Django, and so the vast majority of the deployment steps and considerations for deploying Django are also true for Wagtail. We recommend choosing one of the hosting providers listed below.

## Choosing a Hosting Provider

Several hosting providers offer varying levels of support for Wagtail. We’ve organized them into three categories:

-   Wagtail-level support (easiest deployment).
-   Python-level support (requires some knowledge of WSGI and file storage).
-   Infrastructure-level support (requires knowledge of Linux).

## Wagtail-Level Support

These hosting providers offer first-class support for Wagtail deployments and installations, designed to make it as easy as possible to run a Wagtail site.

### [CodeRed Cloud](https://www.codered.cloud/)

-   Website & pricing: [codered.cloud](https://www.codered.cloud/)
-   Wagtail deployment guide: [CodeRed Wagtail Quickstart](https://www.codered.cloud/docs/wagtail/quickstart/)
-   From the vendor:
    > CodeRed Cloud is inspired by simplicity and “it just works” philosophy. No special packages or 3rd party services required! Free plans are available, and every plan includes a database, media hosting, daily backups, and more.

### [Divio](https://www.divio.com/)

-   Website & pricing: [divio.com](https://www.divio.com/pricing/)
-   Wagtail deployment guide: [Divio Wagtail Setup Guide](https://docs.divio.com/introduction/wagtail/)
-   From the vendor:
    > Divio is a cloud hosting platform designed to simplify the development and deployment of containerized web applications. It integrates smoothly with Wagtail, providing developers with tools to efficiently manage web applications. Divio proactively manages and supports state-of-the-art cloud services, ensuring that your Wagtail applications are scalable, secure, and reliable. The platform’s user-friendly interface makes it easy to develop, deploy, manage, and maintain your web applications. With features like automated backups and staging environments, Divio handles the technical infrastructure, allowing you to focus on building and maintaining your Wagtail sites with confidence.

## Python-Level Support

These hosting providers offer Python environments as a service. Usually, you will need to configure a WSGI server, file storage for media hosting, and a database.

### Fly.io with Backblaze

Read our guide on [deploying to Fly.io](flyio).

## Infrastructure-Level Support

These hosting providers offer the tools needed to run a Linux server, database, file storage, etc. Popular infrastructure providers include: **AWS, Azure, Digital Ocean, Google Cloud, and Linode**.

## Others

Some examples of deployments on a few hosting platforms can be found in [](/advanced_topics/third_party_tutorials). This is not a complete list of platforms where Wagtail can run, nor is it necessarily the only way to run Wagtail there.

For a technical deep-dive into the many aspects of Wagtail hosting, see [](under_the_hood).

---

_Are you a hosting provider who supports Wagtail, and want to add yourself to this list? See if you meet our [requirements for hosting providers](https://github.com/wagtail/wagtail/wiki/Wagtail-Hosting-Providers)._
