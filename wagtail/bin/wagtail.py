#!/usr/bin/env python
import fileinput
import os
import re
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


class UpdateModulePaths(Command):
    description = "Update a Wagtail project tree to use Wagtail 2.x module paths"
    usage = "Usage: %prog updatemodulepaths [root-path]"

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

    def run(self, parser, options, args):
        # Validate args
        if len(args) > 2:
            parser.error("Too many arguments")

        try:
            root_path = args[1]
        except IndexError:
            root_path = os.getcwd()

        checked_count = 0
        changed_count = 0

        for (dirpath, dirnames, filenames) in os.walk(root_path):
            for filename in filenames:
                if not filename.lower().endswith('.py'):
                    continue

                path = os.path.join(dirpath, filename)
                checked_count += 1
                changed = self._rewrite_file(path)
                if changed:
                    print(path)  # NOQA
                    changed_count += 1

        print("\nChecked %d .py files, %d files updated." % (checked_count, changed_count))  # NOQA

    def _rewrite_file(self, filename):
        changed = False

        with fileinput.FileInput(filename, inplace=True) as f:
            for original_line in f:
                line = original_line
                for pattern, repl in self.REPLACEMENTS:
                    line = re.sub(pattern, repl, line)
                print(line, end='')  # NOQA
                if line != original_line:
                    changed = True

        return changed


COMMANDS = {
    'start': CreateProject(),
    'updatemodulepaths': UpdateModulePaths(),
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
