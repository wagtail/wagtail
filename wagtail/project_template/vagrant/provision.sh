#!/bin/bash

PROJECT_NAME=$1

PROJECT_DIR=/home/vagrant/$PROJECT_NAME
VIRTUALENV_DIR=/home/vagrant/.virtualenvs/$PROJECT_NAME

PYTHON=$VIRTUALENV_DIR/bin/python
PIP=$VIRTUALENV_DIR/bin/pip


# Virtualenv setup for project
su - vagrant -c "/usr/local/bin/virtualenv --system-site-packages $VIRTUALENV_DIR && \
    echo $PROJECT_DIR > $VIRTUALENV_DIR/.project && \
    PIP_DOWNLOAD_CACHE=/home/vagrant/.pip_download_cache $PIP install -r $PROJECT_DIR/requirements.txt"

echo "workon $PROJECT_NAME" >> /home/vagrant/.bashrc


# Set execute permissions on manage.py as they get lost if we build from a zip file
chmod a+x $PROJECT_DIR/manage.py


# Run syncdb/migrate/update_index
su - vagrant -c "$PYTHON $PROJECT_DIR/manage.py migrate --noinput && \
                 $PYTHON $PROJECT_DIR/manage.py update_index"


# Add a couple of aliases to manage.py into .bashrc
cat << EOF >> /home/vagrant/.bashrc
alias dj="$PYTHON $PROJECT_DIR/manage.py"
alias djrun="dj runserver 0.0.0.0:8000"
EOF
