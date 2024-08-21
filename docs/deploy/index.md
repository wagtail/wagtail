(deployment_guide)=

# Deploying & Hosting Wagtail

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

### [Divio](https://djtpwt04.eu1.hs-sales-engage.com/Ctc/ZX+23284/djTPWt04/Jks2-6qcW69sMD-6lZ3mWW33N3pF6nlTpxVDmYY_72St44W7WcQZB34Gy_XN564tjxCW9wwW5Qzqq_86S04ZW5kzL9r5ys--sVvWPSq5z_wp5N12NMjlDS290W5xpV801l1QbQW7j0r971B8PwHW1W5N0V4xkzQ6W8FC3C22m3qTjN8DmFHVNg0KDW3cH_jp15CHYGW8h-X0L1qP3r0W8JgZRg7fSp6zW2C1WtR62rTTTW6dpn2Z7GQWB9W5xl4kn8J8lCyW93H_KT1yxPkff1QGBGP04)

-   Website & pricing: [divio.com](https://djtpwt04.eu1.hs-sales-engage.com/Ctc/ZX+23284/djTPWt04/JkM2-6qcW6N1vHY6lZ3pcW2JS-Gx5G-DYfW4MFT8W98G6c6W2DvSTZ7k5hvnF8LfVdx35GmW4T-BzQ2FHjC3N7h3DCyP3BP6W53fnKx7Dp2cwVPnVy56y1fhBW95B9N892LpSlW2BrD5X6hxBcdW6zBY_-42g5FzW4glb7F9hGYY5Vtf9vk8Rkb0CVVCVkz7HrszGN2DfZ1YfDtr4W4rC-NF938nXqW5QxZ__7jcyFDW7Psq7r6CPmPGW3Fgrpq4wKDtkW7BqyqN86tW0tW6jzdpG117J1vW4J69cg1DXj0Vf4bg65P04)
-   Wagtail deployment guide: [Divio Wagtail Setup Guide](https://djtpwt04.eu1.hs-sales-engage.com/Ctc/ZX+23284/djTPWt04/JkM2-6qcW6N1vHY6lZ3pcW2JS-Gx5G-DYfW4MFT8W98G6c6W2DvSTZ7k5hvnF8LfVdx35GmW4T-BzQ2FHjC3N7h3DCyP3BP6W53fnKx7Dp2cwVPnVy56y1fhBW95B9N892LpSlW2BrD5X6hxBcdW6zBY_-42g5FzW4glb7F9hGYY5Vtf9vk8Rkb0CVVCVkz7HrszGN2DfZ1YfDtr4W4rC-NF938nXqW5QxZ__7jcyFDW7Psq7r6CPmPGW3Fgrpq4wKDtkW7BqyqN86tW0tW6jzdpG117J1vW4J69cg1DXj0Vf4bg65P04)
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
