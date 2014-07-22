#!/usr/bin/env bash
# Production-configured Wagtail installation.
# BUT, SECURE SERVICES/ACCOUNT FOR FULL PRODUCTION USE!
# For a non-dummy email backend configure Django's EMAIL_BACKEND
# in settings/production.py post-installation.
# Tested on Ubuntu 13.04 and 13.10.
# Tom Dyson and Neal Todd

PROJECT=mywagtail
PROJECT_ROOT=/usr/local/django

echo "This script overwrites key files, and should only be run on a new box."
read -p "Type 'yes' to confirm: " CONFIRM
[ "$CONFIRM" == "yes" ] || exit

read -p "Enter a name for your project [$PROJECT]: " U_PROJECT
if [ ! -z "$U_PROJECT" ]; then
        PROJECT=$U_PROJECT
fi

read -p "Enter the root of your project, without trailing slash [$PROJECT_ROOT]: " U_PROJECT_ROOT
if [ ! -z "$U_PROJECT_ROOT" ]; then
        PROJECT_ROOT=$U_PROJECT_ROOT
fi

if [ ! -z "$PROJECT_ROOT" ]; then
  mkdir -p $PROJECT_ROOT || exit
fi

echo -e "\nPlease come back in a few minutes, when we'll need you to create an admin account."
sleep 5

SERVER_IP=`ifconfig eth0 |grep "inet addr" | cut -d: -f2 | cut -d" " -f1`

aptitude update
aptitude -y install git python-pip nginx postgresql redis-server
aptitude -y install postgresql-server-dev-all python-dev libjpeg62-dev

perl -pi -e "s/^(local\s+all\s+postgres\s+)peer$/\1trust/" /etc/postgresql/9.1/main/pg_hba.conf
service postgresql reload

aptitude -y install openjdk-7-jre-headless
curl -O https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.0.deb
dpkg -i elasticsearch-1.0.0.deb
rm elasticsearch-1.0.0.deb
perl -pi -e"s/# network.host: 192.168.0.1/network.host: 127.0.0.1/" /etc/elasticsearch/elasticsearch.yml
update-rc.d elasticsearch defaults 95 10
service elasticsearch start

cd $PROJECT_ROOT
git clone https://github.com/torchbox/wagtaildemo.git $PROJECT
cd $PROJECT
mv wagtaildemo $PROJECT
perl -pi -e"s/wagtaildemo/$PROJECT/" manage.py $PROJECT/wsgi.py $PROJECT/settings/*.py
rm -r etc README.md Vagrantfile* .git .gitignore

dd if=/dev/zero of=/tmpswap bs=1024 count=524288
mkswap /tmpswap
swapon /tmpswap
pip install -r requirements/production.txt
swapoff -v /tmpswap
rm /tmpswap

echo SECRET_KEY = \"`python -c 'import random; print "".join([random.SystemRandom().choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])'`\" > $PROJECT/settings/local.py
echo ALLOWED_HOSTS = [\'$SERVER_IP\',] >> $PROJECT/settings/local.py
createdb -Upostgres $PROJECT
./manage.py syncdb --settings=$PROJECT.settings.production
./manage.py migrate --settings=$PROJECT.settings.production
./manage.py update_index --settings=$PROJECT.settings.production
./manage.py collectstatic --settings=$PROJECT.settings.production --noinput

pip install uwsgi
cp $PROJECT/wsgi.py $PROJECT/wsgi_production.py
perl -pi -e"s/($PROJECT.settings)/\1.production/" $PROJECT/wsgi_production.py

curl -O https://raw2.github.com/nginx/nginx/master/conf/uwsgi_params
cat << EOF > /etc/nginx/sites-enabled/default
upstream django {
    server unix://$PROJECT_ROOT/$PROJECT/uwsgi.sock;
}
server {
    listen      80;
    charset     utf-8;
    client_max_body_size 75M; # max upload size
    location /media  {
        alias $PROJECT_ROOT/$PROJECT/media;
    }
    location /static {
        alias $PROJECT_ROOT/$PROJECT/static;
    }
    location / {
        uwsgi_pass  django;
        include     $PROJECT_ROOT/$PROJECT/uwsgi_params;
    }
}
EOF

cat << EOF > $PROJECT_ROOT/$PROJECT/uwsgi_conf.ini
[uwsgi]
chdir           = $PROJECT_ROOT/$PROJECT
module          = $PROJECT.wsgi_production
master          = true
processes       = 10
socket          = $PROJECT_ROOT/$PROJECT/uwsgi.sock
chmod-socket    = 666
vacuum          = true
EOF

mkdir -p /etc/uwsgi/vassals/
ln -s $PROJECT_ROOT/$PROJECT/uwsgi_conf.ini /etc/uwsgi/vassals/

cat << EOF > /etc/init/uwsgi.conf
description "uwsgi for wagtail"
start on runlevel [2345]
stop on runlevel [06]
exec uwsgi --emperor /etc/uwsgi/vassals
EOF

service uwsgi start
service nginx restart

URL="http://$SERVER_IP"
echo -e "\n\nWagtail lives!\n\n"
echo "The public site is at $URL/"
echo "and the admin interface is at $URL/admin/"
