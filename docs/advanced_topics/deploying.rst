Deploying Wagtail
-----------------

On your server
~~~~~~~~~~~~~~

Wagtail is straightforward to deploy on modern Linux-based distributions, but see the section on :doc:`performance </advanced_topics/performance>` for the non-Python services we recommend.

Our current preferences are for Nginx, Gunicorn and supervisor on Debian, but Wagtail should run with any of the combinations detailed in Django's `deployment documentation <https://docs.djangoproject.com/en/dev/howto/deployment/>`_.

On Openshift
~~~~~~~~~~~~

`OpenShift <https://www.openshift.com/>`_ is Red Hat's Platform-as-a-Service (PaaS) that allows developers to quickly develop, host, and scale applications in a cloud environment. With their Python, PostgreSQL and Elasticsearch cartridges there's all you need to host a Wagtail site. To get quickly up and running you may use the `wagtail-openshift-quickstart <https://github.com/texperience/wagtail-openshift-quickstart>`_.

On other PAASs and IAASs
~~~~~~~~~~~~~~~~~~~~~~~~

We know of Wagtail sites running on `Heroku <http://spapas.github.io/2014/02/13/wagtail-tutorial/>`_, Digital Ocean and elsewhere. If you have successfully installed Wagtail on your platform or infrastructure, please :doc:`contribute </contributing/index>` your notes to this documentation!
