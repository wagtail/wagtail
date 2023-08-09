#!/bin/sh
# If you want to run this script inside a vm and save changes outside of it
# You should upgrade watchdog library to the latest in https://github.com/gorakhargosh/watchdog
# and add --debug-force-polling argument to shell-command
# watchmedo shell-command --debug-force-polling --patterns="*.rst" --ignore-pattern='_build/*' --recursive --command='make html; echo "Waiting for more changes..."'

echo "Waiting for you to save the docs..."
watchmedo shell-command --patterns="*.rst" --ignore-pattern='_build/*' --recursive --command='make html; echo "Waiting for more changes..."'
