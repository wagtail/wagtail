#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import os
from optparse import OptionParser

from django.core.management import ManagementUtility


def create_project(parser, options, arguments):
    # Validate args
    if len(arguments) < 2:
        parser.error("Please specify a name for your Wagtail installation")
    elif len(arguments) > 2:
        parser.error("Too many arguments")

    project_name = arguments[1]

    if options.destination:
        destination_dir = options.destination
    else:
        destination_dir = None

    if options.template:
        project_template = options.template
    else:
        project_template = None

    # Make sure given name is not already in use by another python package/module.
    try:
        __import__(project_name)
    except ImportError:
        pass
    else:
        parser.error("'%s' conflicts with the name of an existing "
                     "Python module and cannot be used as a project "
                     "name. Please try another name." % project_name)

    if project_template:
        print("Creating a Wagtail project called %(project_name)s using template from %(project_template)s" % {'project_name': project_name, 'project_template': project_template})  # noqa
    else:
        print("Creating a Wagtail project called %(project_name)s" % {'project_name': project_name})  # noqa

    # Create the project from the Wagtail template using startapp

    # First find the path to Wagtail
    import wagtail
    wagtail_path = os.path.dirname(wagtail.__file__)
    template_path = os.path.join(wagtail_path, 'project_template' if project_template is None else project_template)

    # Call django-admin startproject
    utility_args = ['django-admin.py',
                    'startproject',
                    '--template=' + template_path,
                    '--ext=html,rst',
                    project_name]

    if destination_dir:
        utility_args.append(destination_dir)

    utility = ManagementUtility(utility_args)
    utility.execute()

    print("Success! %(project_name)s has been created" % {'project_name': project_name})  # noqa


COMMANDS = {
    'start': create_project,
}


def main():
    # Parse options
    parser = OptionParser(usage="Usage: %prog start project_name [--destination=<destination_directory>] [--template=<template_path>]")
    parser.add_option("--destination", dest="destination", help="Set destination directory")
    parser.add_option("--template", dest="template", help="Specify a custom template")
    (options, arguments) = parser.parse_args()

    # Find command
    try:
        command = arguments[0]
    except IndexError:
        parser.print_help()
        return

    if command in COMMANDS:
        COMMANDS[command](parser, options, arguments)
    else:
        parser.error("Unrecognised command: " + command)


if __name__ == "__main__":
    main()
