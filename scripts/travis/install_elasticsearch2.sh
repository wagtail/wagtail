#!/bin/bash

sudo apt-get autoremove --purge elasticsearch
wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elk.list
sudo apt-get update && sudo apt-get install elasticsearch -y
sudo service elasticsearch start
