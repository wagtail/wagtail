#!/usr/bin/env python
import fileinput
import fnmatch
import os
import re
import sys
from argparse import ArgumentParser
from difflib import unified_diff

from django.core.management import ManagementUtility


CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 4)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write("This version of Wagtail requires Python {}.{} or above - you are running {}.{}\n".format(*(REQUIRED_PYTHON + CURRENT_PYTHON)))
    sys.exit(1)


def pluralize(value, arg='s'):
    return '' if value == 1 else arg


class Command:
    description = None

    def create_parser(self, command_name=None):
        if command_name is None:
            prog = None
        else:
            # hack the prog name as reported to ArgumentParser to include the command
            prog = "%s %s" % (prog_name(), command_name)

        parser = ArgumentParser(
            description=getattr(self, 'description', None), add_help=False, prog=prog
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        pass

    def print_help(self, command_name):
        parser = self.create_parser(command_name=command_name)
        parser.print_help()

    def execute(self, argv):
        parser = self.create_parser()
        options = parser.parse_args(sys.argv[2:])
        options_dict = vars(options)
        self.run(**options_dict)


class CreateProject(Command):
    description = "Creates the directory structure for a new Wagtail project."

    def add_arguments(self, parser):
        parser.add_argument('project_name', help="Name for your Wagtail project")
        parser.add_argument('dest_dir', nargs='?', help="Destination directory inside which to create the project")

    def run(self, project_name=None, dest_dir=None):
        # Make sure given name is not already in use by another python package/module.
        try:
            __import__(project_name)
        except ImportError:
            pass
        else:
            sys.exit("'%s' conflicts with the name of an existing "
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
                        '--name=Dockerfile',
                        project_name]

        if dest_dir:
            utility_args.append(dest_dir)

        utility = ManagementUtility(utility_args)
        utility.execute()

        print("Success! %(project_name)s has been created" % {'project_name': project_name})  # noqa


class UpdateModulePaths(Command):
    description = "Update a Wagtail project tree to use Wagtail 2.x module paths"

    REPLACEMENTS = [
        (re.compile(r'\bwagtail\.wagtailcore\b'), 'wagtail.core'),
        (re.compile(r'\bwagtail\.wagtailadmin\b'), 'wagtail.admin'),
        (re.compile(r'\bwagtail\.wagtaildocs\b'), 'wagtail.documents'),
        (re.compile(r'\bwagtail\.wagtailembeds\b'), 'wagtail.embeds'),
        (re.compile(r'\bwagtail\.wagtailimages\b'), 'wagtail.images'),
        (re.compile(r'\bwagtail\.wagtailsearch\b'), 'wagtail.search'),
        (re.compile(r'\bwagtail\.wagtailsites\b'), 'wagtail.sites'),
        (re.compile(r'\bwagtail\.wagtailsnippets\b'), 'wagtail.snippets'),
        (re.compile(r'\bwagtail\.wagtailusers\b'), 'wagtail.users'),
        (re.compile(r'\bwagtail\.wagtailforms\b'), 'wagtail.contrib.forms'),
        (re.compile(r'\bwagtail\.wagtailredirects\b'), 'wagtail.contrib.redirects'),
        (re.compile(r'\bwagtail\.contrib\.wagtailfrontendcache\b'), 'wagtail.contrib.frontend_cache'),
        (re.compile(r'\bwagtail\.contrib\.wagtailroutablepage\b'), 'wagtail.contrib.routable_page'),
        (re.compile(r'\bwagtail\.contrib\.wagtailsearchpromotions\b'), 'wagtail.contrib.search_promotions'),
        (re.compile(r'\bwagtail\.contrib\.wagtailsitemaps\b'), 'wagtail.contrib.sitemaps'),
        (re.compile(r'\bwagtail\.contrib\.wagtailstyleguide\b'), 'wagtail.contrib.styleguide'),
    ]

    def add_arguments(self, parser):
        parser.add_argument('root_path', nargs='?', help="Path to your project's root")
        parser.add_argument('--list', action='store_true', dest='list_files', help="Show the list of files to change, without modifying them")
        parser.add_argument('--diff', action='store_true', help="Show the changes that would be made, without modifying the files")
        parser.add_argument(
            '--ignore-dir', action='append', dest='ignored_dirs', metavar='NAME',
            help="Ignore files in this directory"
        )
        parser.add_argument(
            '--ignore-file', action='append', dest='ignored_patterns', metavar='NAME',
            help="Ignore files with this name (supports wildcards)"
        )

    def run(self, root_path=None, list_files=False, diff=False, ignored_dirs=None, ignored_patterns=None):
        if root_path is None:
            root_path = os.getcwd()

        absolute_ignored_dirs = [
            os.path.abspath(dir_path) + os.sep
            for dir_path in (ignored_dirs or [])
        ]

        if ignored_patterns is None:
            ignored_patterns = []

        checked_file_count = 0
        changed_file_count = 0

        for (dirpath, dirnames, filenames) in os.walk(root_path):
            dirpath_with_slash = os.path.abspath(dirpath) + os.sep
            if any(dirpath_with_slash.startswith(ignored_dir) for ignored_dir in absolute_ignored_dirs):
                continue

            for filename in filenames:
                if not filename.lower().endswith('.py'):
                    continue

                if any(fnmatch.fnmatch(filename, pattern) for pattern in ignored_patterns):
                    continue

                path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(path, start=root_path)
                checked_file_count += 1

                if diff:
                    change_count = self._show_diff(path, relative_path=relative_path)
                else:
                    if list_files:
                        change_count = self._count_changes(path)
                    else:  # actually update
                        change_count = self._rewrite_file(path)
                    if change_count:
                        print("%s - %d change%s" % (relative_path, change_count, pluralize(change_count)))  # NOQA

                if change_count:
                    changed_file_count += 1

        if diff or list_files:
            print(
                "\nChecked %d .py file%s, %d file%s to update." % (
                    checked_file_count, pluralize(checked_file_count),
                    changed_file_count, pluralize(changed_file_count)
                )
            )  # NOQA
        else:
            print(
                "\nChecked %d .py file%s, %d file%s updated." % (
                    checked_file_count, pluralize(checked_file_count),
                    changed_file_count, pluralize(changed_file_count)
                )
            )  # NOQA

    def _rewrite_line(self, line):
        for pattern, repl in self.REPLACEMENTS:
            line = re.sub(pattern, repl, line)
        return line

    def _show_diff(self, filename, relative_path=None):
        change_count = 0
        original = []
        updated = []

        with open(filename) as f:
            for original_line in f:
                original.append(original_line)

                line = self._rewrite_line(original_line)
                updated.append(line)
                if line != original_line:
                    change_count += 1

        if change_count:
            relative_path = relative_path or filename

            sys.stdout.writelines(unified_diff(
                original, updated, fromfile="%s:before" % relative_path, tofile="%s:after" % relative_path
            ))

        return change_count

    def _count_changes(self, filename):
        change_count = 0

        with open(filename) as f:
            for original_line in f:
                line = self._rewrite_line(original_line)
                if line != original_line:
                    change_count += 1

        return change_count

    def _rewrite_file(self, filename):
        change_count = 0

        with fileinput.FileInput(filename, inplace=True) as f:
            for original_line in f:
                line = self._rewrite_line(original_line)
                print(line, end='')  # NOQA
                if line != original_line:
                    change_count += 1

        return change_count


COMMANDS = {
    'start': CreateProject(),
    'updatemodulepaths': UpdateModulePaths(),
}


def prog_name():
    return os.path.basename(sys.argv[0])


def help_index():
    print("Type '%s help <subcommand>' for help on a specific subcommand.\n" % prog_name())  # NOQA
    print("Available subcommands:\n")  # NOQA
    for name, cmd in sorted(COMMANDS.items()):
        print("    %s%s" % (name.ljust(20), cmd.description))  # NOQA


def unknown_command(command):
    print("Unknown command: '%s'" % command)  # NOQA
    print("Type '%s help' for usage." % prog_name())  # NOQA
    sys.exit(1)


def main():
    try:
        command_name = sys.argv[1]
    except IndexError:
        help_index()
        return

    if command_name == 'help':
        try:
            help_command_name = sys.argv[2]
        except IndexError:
            help_index()
            return

        try:
            command = COMMANDS[help_command_name]
        except KeyError:
            unknown_command(help_command_name)
            return

        command.print_help(help_command_name)
        return

    try:
        command = COMMANDS[command_name]
    except KeyError:
        unknown_command(command_name)
        return

    command.execute(sys.argv)


if __name__ == "__main__":
    main()
