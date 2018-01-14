#!/usr/bin/env python
import os
from optparse import OptionParser

from django.core.management import ManagementUtility


class Command:
    description = None
    usage = None


class CreateProject(Command):
    description = "Creates the directory structure for a new Wagtail project."
    usage = "Usage: %prog start project_name [directory]"

    def run(self, parser, options, args):
        # Validate args
        if len(args) < 2:
            parser.error("Please specify a name for your Wagtail installation")
        elif len(args) > 3:
            parser.error("Too many arguments")

        project_name = args[1]
        try:
            dest_dir = args[2]
        except IndexError:
            dest_dir = None

        # Make sure given name is not already in use by another python package/module.
        try:
            __import__(project_name)
        except ImportError:
            pass
        else:
            parser.error("'%s' conflicts with the name of an existing "
                         "Python module and cannot be used as a project "
                         "name. Please try another name." % project_name)

        print("Creating a Wagtail project called %(project_name)s" % {'project_name': project_name})  # noqa

        # Create the project from the Wagtail template using startapp

        # First find the path to Wagtail
        import wagtail
        wagtail_path = os.path.dirname(wagtail.__file__)
        template_path = os.path.join(wagtail_path, 'project_template')

        # Call django-admin startproject
        utility_args = ['django-admin.py',
                        'startproject',
                        '--template=' + template_path,
                        '--ext=html,rst',
                        project_name]

        if dest_dir:
            utility_args.append(dest_dir)

        utility = ManagementUtility(utility_args)
        utility.execute()

        print("Success! %(project_name)s has been created" % {'project_name': project_name})  # noqa


COMMANDS = {
    'start': CreateProject(),
}


def main():
    # Set up usage string
    command_descriptions = '\n'.join([
        "    %s%s" % (name.ljust(20), cmd.description)
        for name, cmd in sorted(COMMANDS.items())
        if cmd.description is not None
    ])
    usage = (
        "Usage: %prog <command> [command-options]\n\nAvailable commands:\n\n" +
        command_descriptions
    )

    # Parse options
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    # Find command
    try:
        command = args[0]
    except IndexError:
        parser.print_help()
        return

    if command in COMMANDS:
        command = COMMANDS[command]
        if command.usage is not None:
            parser.set_usage(command.usage)
        command.run(parser, options, args)
    else:
        parser.error("Unrecognised command: " + command)


if __name__ == "__main__":
    main()
