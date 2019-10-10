#!/bin/bash

curl -O https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.4.0-amd64.deb && sudo dpkg -i --force-confnew elasticsearch-7.4.0-amd64.deb && sudo sed -i.old 's/-Xms1g/-Xms128m/' /etc/elasticsearch/jvm.options && sudo sed -i.old 's/-Xmx1g/-Xmx128m/' /etc/elasticsearch/jvm.options && echo -e '-XX:+DisableExplicitGC\n-Djdk.io.permissionsUseCanonicalPath=true\n-Dlog4j.skipJansi=true\n-server\n' | sudo tee -a /etc/elasticsearch/jvm.options && sudo chown -R elasticsearch:elasticsearch /etc/default/elasticsearch && sudo service elasticsearch restart
