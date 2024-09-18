# Deploying Wagtail with Fly.io + Backblaze

This tutorial will use two platforms to deploy your site. You'll host your site on [fly.io](https://fly.io) and serve your site's images on [Backblaze](https://www.backblaze.com).

You can use fly.io to host your site and serve your images. However, storing your images on a platform other than the one hosting your site provides better performance, security, and reliability.

```{note}
In this tutorial, you'll see "yourname" several times. Replace it with a name of your choice.
```

## Setup Backblaze B2 Cloud Storage

To serve your images, set up a Backblaze B2 storage following these steps:

1. Visit the Backblaze [website](https://www.backblaze.com) in your browser.
2. Click **Products** from the top navigation and then select **B2 Cloud Storage** from the dropdown.
3. Sign up to Backblaze B2 Cloud Storage by following these steps:

    a. Enter your email address and password.
    b. Select the appropriate region.
    c. Click **Sign Up Now**.

4. Verify your email by following these steps:

    a. Go to **Account > My Settings** in your side navigation.
    b. Click **Verify Email** in the **Security section**.
    c. Enter your sign-up email address and then click send **Send Code**.
    d. Check your email inbox or spam folder for the verification email.
    e. Click the verification link or use the verification code.

5. Create a Bucket by going to **B2 Cloud Storage > Bucket** and clicking **Create a Bucket**.
6. Go to **B2 Cloud Storage > Bucket** and then click **Create a Bucket**.
7. Add your Bucket information as follows:

| Bucket information  | Instruction                                                        |
| ------------------- | ------------------------------------------------------------------ |
| Bucket Unique Name  | Use a unique Bucket name. For example,_yourname-wagtail-portfolio_ |
| Files in Bucket are | Select **Public**                                                  |
| Default Encryption  | Select **Disable**                                                 |
| Object Lock         | Select **Disable**                                                 |

8. Click **Create a Bucket**.

## Link your site to Backblaze B2 Cloud Storage

After setting up your Backblaze B2 Cloud Storage, you must link it to your portfolio site.

Start by creating a `.env.production` file at the root of your project directory. At this stage, your project directory should look like this:

```text
mysite/
├── base
├── blog
├── home
├── media
├── mysite
├── portfolio
├── search
├── .dockerignore
├── .gitignore
├── .env.production
├── Dockerfile
├── manage.py
├── mysite/
└── requirements.txt
```

Now add the following environment variables to your `.env.production` file:

```text
AWS_STORAGE_BUCKET_NAME=
AWS_S3_ENDPOINT_URL=https://
AWS_S3_REGION_NAME=
AWS_S3_ACCESS_KEY_ID=
AWS_S3_SECRET_ACCESS_KEY=
DJANGO_ALLOWED_HOSTS=
DJANGO_CSRF_TRUSTED_ORIGINS=https://
DJANGO_SETTINGS_MODULE=mysite.settings.production
```

### Fill in your Backblaze B2 bucket information

The next step is to provide values for your environment variables. In your `.env.production` file, use your Backblaze B2 bucket information as values for your environment variables as follows:

| Environment variable        | Instruction                                                                                                                                                             |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AWS_STORAGE_BUCKET_NAME     | Use your Backblaze B2 bucket name                                                                                                                                       |
| AWS_S3_ENDPOINT_URL         | Use the Backblaze B2 endpoint URL. For example, _https://s3.us-east-005.backblazeb2.com_                                                                                |
| AWS_S3_REGION_NAME          | Determine your bucket's region from the endpoint URL. For example, if your endpoint URL is _s3.us-east-005.backblazeb2.com_, then your bucket's region is _us-east-005_ |
| AWS_S3_ACCESS_KEY_ID        | Leave this empty for now                                                                                                                                                |
| AWS_S3_SECRET_ACCESS_KEY    | Leave this empty for now                                                                                                                                                |
| DJANGO_ALLOWED_HOSTS        | Leave this empty for now                                                                                                                                                |
| DJANGO_CSRF_TRUSTED_ORIGINS | Use _https://_                                                                                                                                                          |
| DJANGO_SETTINGS_MODULE      | Use _mysite.settings.production_                                                                                                                                        |

In the preceding table, you didn't provide values for your `AWS_S3_ACCESS_KEY_ID`, `AWS_S3_SECRET_ACCESS_KEY`, and `DJANGO_ALLOWED_HOSTS`.

To get values for your `AWS_S3_ACCESS_KEY_ID` and `AWS_S3_SECRET_ACCESS_KEY`, follow these steps:

1. Log in to your Backblaze B2 account.
2. Navigate to **Account > Application Keys**.
3. Click **Add a New Application Key**.
4. Configure the application key settings as follows:

| Setting                     | Instruction                                        |
| --------------------------- | -------------------------------------------------- |
| Name of Key                 | Provide a unique name                              |
| Allow access to Buckets     | Choose the Backblaze B2 bucket you created earlier |
| Type of Access              | Select **Read and Write**                          |
| Allow List All Bucket Names | Leave this unticked                                |
| File name prefix            | Leave field empty                                  |
| Duration (seconds)          | Leave field empty                                  |

5. Click **Create New Key**.

Now, use your `keyID` as the value of `AWS_S3_ACCESS_KEY_ID` and `applicationKey` for `AWS_S3_SECRET_ACCESS_KEY` in your `.env.production` file:

| Environment variable     | Instruction                 |
| ------------------------ | --------------------------- |
| AWS_S3_ACCESS_KEY_ID     | Use your **keyID**          |
| AWS_S3_SECRET_ACCESS_KEY | Use your **applicationKey** |

At this stage, the content of your `.env.production` file looks like this:

```text
AWS_STORAGE_BUCKET_NAME=yourname-wagtail-portfolio
AWS_S3_ENDPOINT_URL=https://s3.us-east-005.backblazeb2.com
AWS_S3_REGION_NAME=us-east-005
AWS_S3_ACCESS_KEY_ID=your Backblaze keyID
AWS_S3_SECRET_ACCESS_KEY=your Backblaze applicationKey
DJANGO_ALLOWED_HOSTS=
DJANGO_CSRF_TRUSTED_ORIGINS=https://
DJANGO_SETTINGS_MODULE=mysite.settings.production
```

```{note}
The Backblaze B2 storage uses _AWS_ and _S3_ because it works like Amazon Web Services’ S3.

Do not commit or share your `.env.production `file. Anyone with the variables can access your site.

If you lost your secret application key, create a new key following the preceding instructions.
```

For more information on how to set up your Backblaze B2 Cloud Storage, read the [Backblaze B2 Cloud Storage Documentation](https://www.backblaze.com/docs/cloud-storage/).

## Set up Fly.io

Now that you've linked your site to your Backblaze storage, it's time to set up Fly.io to host your site.

To set up your Fly.io account, follow these steps:

1. Visit [Fly.io](https://fly.io/) in your browser.
2. Click **Sign Up**.
3. Sign up using your GitHub account, Google account, or the email option.
4. Check your email inbox for the verification link to verify your email.

```{note}
If your email verification fails, go to your Fly.io [Dashboard](https://fly.io/dashboard) and try again.
```

5. Go to **Dashboard > Billing** and click **Add credit card** to add your credit card.

```{note}
Adding your credit card allows you to create a project in Fly.io. Fly.io won't charge you after adding your credit card.
```

6. [Install flyctl](https://fly.io/docs/hands-on/install-flyctl/) by navigating to your project directory and then running the following command in your terminal:

On macOS:

```sh
# If you have the Homebrew package manager installed, run the following command:
brew install flyctl

# If you don't have the Homebrew package manager installed, run the following command:
curl -L https://fly.io/install.sh | sh
```

On Linux:

```sh
curl -L https://fly.io/install.sh | sh
```

On Windows, navigate to your project directory on **PowerShell**, activate your environment and run the following command:

```doscon
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

```{note}
If you get an error on Windows saying the term `pwsh` is  not recognized, install [PowerShell MSI](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.3#installing-the-msi-package) and then rerun the preceding Windows command.
```

7. [Sign in](https://fly.io/docs/hands-on/sign-in/) to your Fly.io by running the following command:

```sh
fly auth login
```

If you use Microsoft WSL, then run:

```doscon
ln -s /usr/bin/wslview /usr/local/bin/xdg-open
```

```{note}
If you successfully install flyctl but get an error saying "`fly` is not recognized" or "flyctl: command not found error", then you must add flyctl to your PATH. For more information, read [Getting flyctl: command not found error post install](https://community.fly.io/t/getting-flyctl-command-not-found-error-post-install/4954/1).
```

8. Create your Fly.io project by running `fly launch`. Then press `y` to configure the settings.
9. You will be taken to an admin screen on fly.io. Fill out the fields as follows:

| Field                          | Instruction                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| Choose a region for deployment | Select the region closest to the _AWS_S3_REGION_NAME_ in your _env.production_ file. |
| CPU & Memory                   | VM Size - shared-cpu-1x VM Memory - 512 MB                                           |
| Database                       | Fly Postgres - choose smallest option                                                |

click confirm **Confirm settings**

```{note}
Not creating the database directly with the application leads to the app and the database not connected.
If the app is going to be launched again using fly launch,
it's recommended to create a new database with the launch of the app through the web UI.
```

10. Back in your terminal, answer the resulting prompt questions as follows:

| Question                       | Instruction |
| ------------------------------ | ----------- |
| Overwrite ".../.dockerignore"? | Enter _y_   |
| Overwrite ".../Dockerfile"?    | Enter _y_   |

The `fly launch` command creates two new files, `Dockerfile` and `fly.toml`, in your project directory.

If you use a third-party app terminal like the Visual Studio Code terminal, you may get an error creating your Postgres database. To rectify this error, follow these steps:

1. Delete `fly.toml` file from your project directory.
2. Go to your Fly.io account in your browser and click **Dashboard**.
3. Click the created app in your **Apps** list.
4. Click **Settings** in your side navigation.
5. Click **Delete app**.
6. Enter the name your app.
7. Click **Yes delete it**.
8. Repeat steps 3, 4, 5, 6, and 7 for all apps in your **Apps** list.
9. Run the `fly launch` command in your built-in terminal or PowerShell MSI on Windows.

## Customize your site to use Fly.io

Now, you must configure your portfolio site for the final deployment.

The `fly launch` command creates two new files, `Dockerfile` and `fly.toml`, in your project directory.

Add the following to your `.gitignore` file to make Git ignore your environment files:

```
.env*
```

Also, add the following to your `.dockerignore` file to make Docker ignore your environment and media files:

```
.env*
media
```

Configure your Fly.io to use `1` worker. This allows your site to work better with Fly.io's low memory allowance. To do this, modify the last line of your `Dockerfile` as follows:

```
CMD ["gunicorn", "--bind", ":8000", "--workers", "1", "mysite.wsgi"]
```

Also, check if your `fly.toml` file has the following:

```toml
[deploy]
  release_command = "python manage.py migrate --noinput"
```

Your `fly.toml` file should look as follows:

```toml
app = "yourname-wagtail-portfolio"
primary_region = "lhr"
console_command = "/code/manage.py shell"

[build]

# add the deploy command:
[deploy]
  release_command = "python manage.py migrate --noinput"

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0
  processes = ["app"]

[[statics]]
  guest_path = "/code/static"
  url_prefix = "/static/"
```

Now add your production dependencies by replacing the content of your `requirements.txt` file with the following:

```text
Django>=4.2,<4.3
wagtail==5.1.1
gunicorn>=21.2.0,<22.0.0
psycopg[binary]>=3.1.10,<3.2.0
dj-database-url>=2.1.0,<3.0.0
whitenoise>=5.0,<5.1
django-storages[s3]>=1.14.0,<2.0.0
```

The preceding dependencies ensure that the necessary tools and libraries are in place to run your site successfully on the production server. The following are the explanations for the dependencies you may be unaware of:

1. `gunicorn` is a web server that runs your site in Docker.
2. `psycopg` is a PostgreSQL adapter that connects your site to a PostgreSQL database.
3. `dj-database-url` is a package that simplifies your database configurations and connects to your site to a PostgreSQL database.
4. `whitenoise` is a Django package that serves static files.
5. `django-storages` is a Django library that handles your file storage and connects to your Backblaze B2 storage.

Replace the content of your `mysite/settings/production.py` file with the following:

```python
import os
import random
import string
import dj_database_url

from .base import *

DEBUG = False

DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True
    )
}

SECRET_KEY = os.environ["SECRET_KEY"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = True

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MIDDLEWARE.append("whitenoise.middleware.WhiteNoiseMiddleware")
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

if "AWS_STORAGE_BUCKET_NAME" in os.environ:
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY")

    INSTALLED_APPS.append("storages")

    STORAGES["default"]["BACKEND"] = "storages.backends.s3boto3.S3Boto3Storage"

    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    },
}

WAGTAIL_REDIRECTS_FILE_STORAGE = "cache"

try:
    from .local import *
except ImportError:
    pass
```

The explanation of some of the code in your `mysite/settings/production.py` file is as follows:

1. `DEBUG = False` turns off debugging for the production environment. It's important for security and performance.
2. `SECRET_KEY = os.environ["SECRET_KEY"]` retrieves the project's secret key from your environment variable.
3. `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` ensures that Django can detect a secure HTTPS connection if you deploy your site behind a reverse proxy like Heroku.
4. `SECURE_SSL_REDIRECT = True` enforces HTTPS redirect. This ensures that all connections to the site are secure.
5. `ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")` defines the hostnames that can access your site. It retrieves its values from the `DJANGO_ALLOWED_HOSTS` environment variable. If no specific hosts are defined, it defaults to allowing all hosts.
6. `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` configures your site to use the console email backend. You can configure this to use a proper email backend for sending emails.
7. `WAGTAIL_REDIRECTS_FILE_STORAGE = "cache"` configures the file storage for Wagtail's redirects. Here, you set it to use cache.

Now, complete the configuration of your environment variables by modifying your `.env.production` file as follows:

| Environment variable        | Instruction                                                                                           |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| DJANGO_ALLOWED_HOSTS        | This must match your fly.io project name. For example, _yourname-wagtail-portfolio.fly.dev_           |
| DJANGO_CSRF_TRUSTED_ORIGINS | This must match your project’s domain name. For example, _https://yourname-wagtail-portfolio.fly.dev_ |

The content of your `.env.production` file should now look like this:

```text
AWS_STORAGE_BUCKET_NAME=yourname-wagtail-portfolio
AWS_S3_ENDPOINT_URL=https://s3.us-east-005.backblazeb2.com
AWS_S3_REGION_NAME=us-east-005
AWS_S3_ACCESS_KEY_ID=your Backblaze keyID
AWS_S3_SECRET_ACCESS_KEY=your Backblaze applicationKey
DJANGO_ALLOWED_HOSTS=yourname-wagtail-portfolio.fly.dev
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourname-wagtail-portfolio.fly.dev
DJANGO_SETTINGS_MODULE=mysite.settings.production
```

Set the secrets for Fly.io to use by running:

```sh
flyctl secrets import < .env.production
```

On Windows, run the following command in your PowerShell MSI:

```doscon
Get-Content .env.production | flyctl secrets import
```

Finally, deploy your site to Fly.io by running the following command:

```sh
fly deploy --ha=false
```

```{note}
Running "fly deploy" creates two machines for your app. Using the "--ha=false" flag creates one machine for your app.
```

Congratulations! Your site is now live. However, you must add content to it. Start by creating an admin user for your live site. Run the following command:

```sh
flyctl ssh console
```

Then run:

```sh
DJANGO_SUPERUSER_USERNAME=username DJANGO_SUPERUSER_EMAIL=mail@example.com DJANGO_SUPERUSER_PASSWORD=password python manage.py createsuperuser --noinput
```

```{note}
Ensure you replace _username_, _mail@example.com_, and _password_ with a username, email address, and password of your choice.
```

For more information on how to set up your Django project on Fly.io, read [Django on Fly.io](https://fly.io/docs/django/).

## Add content to your live site

All this while, you've been adding content to your site in the local environment. Now that your site is live on a server, you must add content to the live site. To add content to your live site, go to ` https://yourname-wagtail-portfolio.fly.dev/admin/` in your browser and follow the steps in the following sub-sections of the tutorial:

-   [Add content to your homepage](add_content_to_your_homepage)
-   [Add your social media links](add_your_social_media_links)
-   [Add footer text](add_footer_text)
-   [Add pages to your site menu](add_pages_to_your_site_menu)
-   [Add your contact information](add_your_contact_information)
-   [Add your resume](add_your_resume)

```{note}
If you encounter errors while trying to access your live site in your browser, check your application logs in your Fly.io Dashboard. To check your application logs, click **Dashboard > Apps > yourname-wagtail-portfolio > Monitoring**
```
