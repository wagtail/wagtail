(deployment_docker)=

# Deploying with Docker

The default project template includes a Dockerfile. Its default command starts Gunicorn. Run database migrations separately, once per deployment, before starting or updating the application containers.

## Configure your project

Before building the image, configure your project for deployment following [](under_the_hood) and Django's [deployment checklist](inv:django#howto/deployment/checklist).

The migration container and application containers must use the same Django settings and database. Configure the `DATABASES` setting to connect to a persistent database accessible to all of these containers. If your settings read environment variables for database credentials or other secrets, pass those variables to both commands below. The default project template does not automatically read a `DATABASE_URL` environment variable.

The default SQLite database is stored inside the container. Running migrations in a temporary container with this default would discard the database when the container exits. If you use SQLite, configure its path in a persistent volume and mount that same volume, with write access for the `wagtail` user, in both the migration and application containers.

Create an environment file outside the Docker build context, for example `../deployment.env`, containing the environment variables your settings require. Pass it to the migration and application containers as shown below.

## Build the image

The Dockerfile sets `DJANGO_SETTINGS_MODULE` to your project's production settings for both build commands and the application server. It runs `collectstatic` during the build using these settings, which configure `ManifestStaticFilesStorage` by default. If you customize the settings, ensure they can be loaded during the build and use the same static file storage configuration at runtime. Do not copy production secrets into the image.

From the generated project's directory, build an image for the release:

```sh
docker build --tag mysite:latest .
```

Replace `mysite` with your project name. Use the same image for migrations and application containers.

## Run migrations before starting the server

Run migrations in a temporary container:

```sh
docker run --rm --env-file ../deployment.env mysite:latest python manage.py migrate --noinput
```

This overrides the image's default server command. Wait for the command to finish successfully before starting or updating any application containers. If it fails, stop the deployment and resolve the error before retrying.

Then start the server:

```sh
docker run --detach --name mysite --env-file ../deployment.env --publish 8000:8000 mysite:latest
```

Add any network and volume options required by your deployment to both commands. Configure static file and uploaded media storage as described in [](under_the_hood).

For a declarative way to configure services, networks, and volumes, use [Docker Compose](https://docs.docker.com/compose/). Run migrations as a separate step before starting or updating the application services.

For automated deployments, use your hosting platform's release command or a single deployment job to run `python manage.py migrate --noinput` with the new image. Make successful completion of that job a prerequisite for rolling out application containers. Do not run migrations independently in each replica's startup command: multiple replicas may attempt the same migration concurrently.

Starting, restarting, or scaling the application containers does not need to run migrations. When rolling out a new release while old containers are still serving requests, ensure its migrations are compatible with the old application code, or schedule downtime for the migration and rollout.
