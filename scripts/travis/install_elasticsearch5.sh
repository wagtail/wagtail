#!/bin/bash

sudo sysctl -w vm.max_map_count=262144

sudo apt-get autoremove --purge elasticsearch
wget -P /tmp/ https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.3.3.deb
sudo dpkg -i /tmp/elasticsearch-5.3.3.deb
sudo service elasticsearch start
