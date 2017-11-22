#!/bin/bash

curl -O https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.6/elasticsearch-2.4.6.deb && sudo dpkg -i --force-confnew elasticsearch-2.4.6.deb && sudo service elasticsearch restart
