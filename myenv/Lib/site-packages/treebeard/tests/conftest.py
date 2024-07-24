"""Pytest configuration file
"""
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "treebeard.tests.settings"

import django


def pytest_report_header(config):
    return "Django: " + django.get_version()


def pytest_configure(config):
    django.setup()
