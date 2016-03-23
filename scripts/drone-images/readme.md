Wagtail CI base images
======================

This directory contains Dockerfiles for building the base images used by
Wagtail's continuous integration server.


Building
--------

Run the following commands to build all the images:

    docker build -t wagtail-flake8 flake8
    docker build -t wagtail-jscs jscs
    docker build -t wagtail-scss-lint scss-lint
