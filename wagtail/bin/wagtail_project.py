#!/usr/bin/env python
import os
import subprocess
import errno
import sys

from optparse import OptionParser

TEMPLATE_NAME = 'wagtaildemo'  # the name of the folder in wagtail/library


def replace_strings_in_file(filename, old_string, new_string):
    f = open(filename, 'r')
    filedata = f.read()
    f.close()

    newdata = filedata.replace(old_string, new_string)

    f = open(filename, 'w')
    f.write(newdata)
    f.close()


def create_project():

    # collect and analyse the name given for the wagtail project
    parser = OptionParser(usage="Usage: %prog project_name")
    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("Please specify a name for your wagtail installation")

    project_name = args[0]
    project_path = os.path.join(os.getcwd(), project_name)

    # Make sure given name is not already in use by another python package/module.
    try:
        __import__(project_name)
    except ImportError:
        pass
    else:
        parser.error("'%s' conflicts with the name of an existing "
                     "Python module and cannot be used as a project "
                     "name. Please try another name." % project_name)

    # make sure directory does not already exist
    if os.path.exists(project_name):
        print 'A directory called %(project_name)s already exists. \
            Please choose another name for your wagtail project or remove the existing directory.' % {'project_name': project_name}
        sys.exit(errno.EEXIST)

    print "Creating a wagtail project called %(project_name)s" % {'project_name': project_name}

    # create the project from the wagtail template using startapp

    # first find the path to wagtail
    import wagtail
    wagtail_path = os.path.dirname(wagtail.__file__)
    template_path = os.path.join(wagtail_path, 'library', TEMPLATE_NAME)

    # call django-admin startproject
    subprocess.call(['django-admin.py', 'startproject', '--template=' + template_path, project_name])

    # in newly created project, replace all occurences of TEMPLATE_NAME ('wagtaildemo')
    os.chdir(project_name)

    # first within the contents of files
    for folder, subs, files in os.walk(os.getcwd()):
        for filename in files:
            replace_strings_in_file(os.path.join(folder, filename), TEMPLATE_NAME, project_name)

    # then in file and folder names
    for folder, subs, files in os.walk(os.getcwd()):
        for sub in subs:
            if TEMPLATE_NAME in sub:
                os.rename(sub, sub.replace(TEMPLATE_NAME, project_name))
        for filename in files:
            if TEMPLATE_NAME in filename:
                os.rename(filename, filename.replace(TEMPLATE_NAME, project_name))

    print 'Success! %(project_name)s is created' % {'project_name': project_name}

if __name__ == "__main__":
    create_project()
