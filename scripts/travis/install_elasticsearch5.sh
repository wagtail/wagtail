#!/bin/bash

curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.3.3.deb && sudo dpkg -i --force-confnew elasticsearch-5.3.3.deb && sudo service elasticsearch restart
