#!/bin/bash

curl -O https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.7.6.deb && sudo dpkg -i --force-confnew elasticsearch-1.7.6.deb && sudo service elasticsearch restart
