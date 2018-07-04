#!/bin/bash

curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-6.1.0.deb && sudo dpkg -i --force-confnew elasticsearch-6.1.0.deb && sudo service elasticsearch restart
