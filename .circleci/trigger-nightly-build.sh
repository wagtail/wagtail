#!/bin/bash
# Triggers a nightly build for the latest commit on main
# Use this for testing changes to the nightly release process
# Call with the CIRCLE_API_USER_TOKEN set to your Personal API key
# You can find this under User Settings on Circle CI

curl -u ${CIRCLE_API_USER_TOKEN}: \
     -d build_parameters[CIRCLE_JOB]=nightly-build \
     https://circleci.com/api/v1.1/project/github/wagtail/wagtail/tree/main
