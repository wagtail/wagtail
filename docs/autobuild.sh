#!/bin/sh

echo "Waiting for you to save the docs..."
watchmedo shell-command --patterns="*.rst" --ignore-pattern='_build/*' --recursive --command='make html; echo "Waiting for more changes..."'
