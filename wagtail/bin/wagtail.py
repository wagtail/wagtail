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
REQUIRED_PYTHON = (3, 7)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write(
        "This version of Wagtail requires Python {}.{} or above - you are running {}.{}\n".format(
            *(REQUIRED_PYTHON + CURRENT_PYTHON)
        )
    )
    sys.exit(1)


def pluralize(value, arg="s"):
    return "" if value == 1 else arg


class Command:
    description = None

    def create_parser(self, command_name=None):
        if command_name is None:
            prog = None
        else:
            # hack the prog name as reported to ArgumentParser to include the command
            prog = f"{prog_name()} {command_name}"

        parser = ArgumentParser(
            description=getattr(self, "description", None), add_help=False, prog=prog
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

    def __init__(self):
        self.default_template_path = self.get_default_template_path()

    def add_arguments(self, parser):
        parser.add_argument("project_name", help="Name for your Wagtail project")
        parser.add_argument(
            "dest_dir",
            nargs="?",
            help="Destination directory inside which to create the project",
        )
        parser.add_argument(
            "--template",
            help="The path or URL to load the template from.",
            default=self.default_template_path,
        )

    def get_default_template_path(self):
        import wagtail

        wagtail_path = os.path.dirname(wagtail.__file__)
        default_template_path = os.path.join(wagtail_path, "project_template")
        return default_template_path

    def run(self, project_name=None, dest_dir=None, **options):
        # Make sure given name is not already in use by another python package/module.
        try:
            __import__(project_name)
        except ImportError:
            pass
        else:
            sys.exit(
                "'%s' conflicts with the name of an existing "
                "Python module and cannot be used as a project "
                "name. Please try another name." % project_name
            )

        template_name = options["template"]
        if template_name == self.default_template_path:
            template_name = "the default Wagtail template"

        print(  # noqa: T201
            "Creating a Wagtail project called %(project_name)s using %(template_name)s"
            % {"project_name": project_name, "template_name": template_name}
        )

        # Call django-admin startproject
        utility_args = [
            "django-admin",
            "startproject",
            "--template=" + options["template"],
            "--ext=html,rst",
            "--name=Dockerfile",
            project_name,
        ]

        if dest_dir:
            utility_args.append(dest_dir)

        utility = ManagementUtility(utility_args)
        utility.execute()

        print(  # noqa: T201
            "Success! %(project_name)s has been created"
            % {"project_name": project_name}
        )


class UpdateModulePaths(Command):
    description = "Update a Wagtail project tree to use Wagtail 2.x module paths"

    REPLACEMENTS = [
        # Added in Wagtail 2.0
        (re.compile(r"\bwagtail\.wagtailcore\b"), "wagtail"),
        (re.compile(r"\bwagtail\.wagtailadmin\b"), "wagtail.admin"),
        (re.compile(r"\bwagtail\.wagtaildocs\b"), "wagtail.documents"),
        (re.compile(r"\bwagtail\.wagtailembeds\b"), "wagtail.embeds"),
        (re.compile(r"\bwagtail\.wagtailimages\b"), "wagtail.images"),
        (re.compile(r"\bwagtail\.wagtailsearch\b"), "wagtail.search"),
        (re.compile(r"\bwagtail\.wagtailsites\b"), "wagtail.sites"),
        (re.compile(r"\bwagtail\.wagtailsnippets\b"), "wagtail.snippets"),
        (re.compile(r"\bwagtail\.wagtailusers\b"), "wagtail.users"),
        (re.compile(r"\bwagtail\.wagtailforms\b"), "wagtail.contrib.forms"),
        (re.compile(r"\bwagtail\.wagtailredirects\b"), "wagtail.contrib.redirects"),
        (
            re.compile(r"\bwagtail\.contrib\.wagtailfrontendcache\b"),
            "wagtail.contrib.frontend_cache",
        ),
        (
            re.compile(r"\bwagtail\.contrib\.wagtailroutablepage\b"),
            "wagtail.contrib.routable_page",
        ),
        (
            re.compile(r"\bwagtail\.contrib\.wagtailsearchpromotions\b"),
            "wagtail.contrib.search_promotions",
        ),
        (
            re.compile(r"\bwagtail\.contrib\.wagtailsitemaps\b"),
            "wagtail.contrib.sitemaps",
        ),
        (
            re.compile(r"\bwagtail\.contrib\.wagtailstyleguide\b"),
            "wagtail.contrib.styleguide",
        ),
        # Added in Wagtail 3.0
        (re.compile(r"\bwagtail\.tests\b"), "wagtail.test"),
        (re.compile(r"\bwagtail\.core\.utils\b"), "wagtail.coreutils"),
        (re.compile(r"\bwagtail\.core\b"), "wagtail"),
        (re.compile(r"\bwagtail\.admin\.edit_handlers\b"), "wagtail.admin.panels"),
        (
            re.compile(r"\bwagtail\.contrib\.forms\.edit_handlers\b"),
            "wagtail.contrib.forms.panels",
        ),
    ]

    def add_arguments(self, parser):
        parser.add_argument("root_path", nargs="?", help="Path to your project's root")
        parser.add_argument(
            "--list",
            action="store_true",
            dest="list_files",
            help="Show the list of files to change, without modifying them",
        )
        parser.add_argument(
            "--diff",
            action="store_true",
            help="Show the changes that would be made, without modifying the files",
        )
        parser.add_argument(
            "--ignore-dir",
            action="append",
            dest="ignored_dirs",
            metavar="NAME",
            help="Ignore files in this directory",
        )
        parser.add_argument(
            "--ignore-file",
            action="append",
            dest="ignored_patterns",
            metavar="NAME",
            help="Ignore files with this name (supports wildcards)",
        )

    def run(
        self,
        root_path=None,
        list_files=False,
        diff=False,
        ignored_dirs=None,
        ignored_patterns=None,
    ):
        if root_path is None:
            root_path = os.getcwd()

        absolute_ignored_dirs = [
            os.path.abspath(dir_path) + os.sep for dir_path in (ignored_dirs or [])
        ]

        if ignored_patterns is None:
            ignored_patterns = []

        checked_file_count = 0
        changed_file_count = 0

        for dirpath, dirnames, filenames in os.walk(root_path):
            dirpath_with_slash = os.path.abspath(dirpath) + os.sep
            if any(
                dirpath_with_slash.startswith(ignored_dir)
                for ignored_dir in absolute_ignored_dirs
            ):
                continue

            for filename in filenames:
                if not filename.lower().endswith(".py"):
                    continue

                if any(
                    fnmatch.fnmatch(filename, pattern) for pattern in ignored_patterns
                ):
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
                        print(  # noqa: T201
                            "%s - %d change%s"
                            % (relative_path, change_count, pluralize(change_count))
                        )

                if change_count:
                    changed_file_count += 1

        if diff or list_files:
            print(  # noqa: T201
                "\nChecked %d .py file%s, %d file%s to update."
                % (
                    checked_file_count,
                    pluralize(checked_file_count),
                    changed_file_count,
                    pluralize(changed_file_count),
                )
            )
        else:
            print(  # noqa: T201
                "\nChecked %d .py file%s, %d file%s updated."
                % (
                    checked_file_count,
                    pluralize(checked_file_count),
                    changed_file_count,
                    pluralize(changed_file_count),
                )
            )

    def _rewrite_line(self, line):
        for pattern, repl in self.REPLACEMENTS:
            line = re.sub(pattern, repl, line)
        return line

    def _show_diff(self, filename, relative_path=None):
        change_count = 0
        found_unicode_error = False
        original = []
        updated = []

        with open(filename, mode="rb") as f:
            for raw_original_line in f:
                try:
                    original_line = raw_original_line.decode("utf-8")
                except UnicodeDecodeError:
                    found_unicode_error = True
                    # retry decoding as utf-8, mangling invalid bytes so that we have a usable string to use the diff
                    line = original_line = raw_original_line.decode(
                        "utf-8", errors="replace"
                    )
                else:
                    line = self._rewrite_line(original_line)

                original.append(original_line)
                updated.append(line)
                if line != original_line:
                    change_count += 1

        if found_unicode_error:
            sys.stderr.write(
                "Warning - %s is not a valid UTF-8 file. Lines with decode errors have been ignored\n"
                % filename
            )

        if change_count:
            relative_path = relative_path or filename

            sys.stdout.writelines(
                unified_diff(
                    original,
                    updated,
                    fromfile="%s:before" % relative_path,
                    tofile="%s:after" % relative_path,
                )
            )

        return change_count

    def _count_changes(self, filename):
        change_count = 0
        found_unicode_error = False

        with open(filename, mode="rb") as f:
            for raw_original_line in f:
                try:
                    original_line = raw_original_line.decode("utf-8")
                except UnicodeDecodeError:
                    found_unicode_error = True
                else:
                    line = self._rewrite_line(original_line)
                    if line != original_line:
                        change_count += 1

        if found_unicode_error:
            sys.stderr.write(
                "Warning - %s is not a valid UTF-8 file. Lines with decode errors have been ignored\n"
                % filename
            )

        return change_count

    def _rewrite_file(self, filename):
        change_count = 0
        found_unicode_error = False

        with fileinput.FileInput(filename, inplace=True, mode="rb") as f:
            for raw_original_line in f:
                try:
                    original_line = raw_original_line.decode("utf-8")
                except UnicodeDecodeError:
                    sys.stdout.write(raw_original_line)
                    found_unicode_error = True
                else:
                    line = self._rewrite_line(original_line)
                    if CURRENT_PYTHON >= (3, 8):
                        sys.stdout.write(line.encode("utf-8"))
                    else:
                        # Python 3.7 opens the output stream in text mode, so write the line back as
                        # text rather than bytes:
                        # https://github.com/python/cpython/commit/be6dbfb43b89989ccc83fbc4c5234f50f44c47ad
                        sys.stdout.write(line)

                    if line != original_line:
                        change_count += 1

        if found_unicode_error:
            sys.stderr.write(
                "Warning - %s is not a valid UTF-8 file. Lines with decode errors have been ignored\n"
                % filename
            )

        return change_count


class Version(Command):
    description = "List which version of Wagtail you are using"

    def run(self):
        import wagtail

        version = wagtail.get_version(wagtail.VERSION)

        print(f"You are using Wagtail {version}")  # noqa: T201


COMMANDS = {
    "start": CreateProject(),
    "updatemodulepaths": UpdateModulePaths(),
    "--version": Version(),
}


def prog_name():
    return os.path.basename(sys.argv[0])


def help_index():
    print(  # noqa: T201
        "Type '%s help <subcommand>' for help on a specific subcommand.\n" % prog_name()
    )
    print("Available subcommands:\n")  # NOQA: T201
    for name, cmd in sorted(COMMANDS.items()):
        print(f"    {name.ljust(20)}{cmd.description}")  # NOQA: T201


def unknown_command(command):
    print("Unknown command: '%s'" % command)  # NOQA: T201
    print("Type '%s help' for usage." % prog_name())  # NOQA: T201
    sys.exit(1)


def main():
    try:
        command_name = sys.argv[1]
    except IndexError:
        help_index()
        return

    if command_name == "help":
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
