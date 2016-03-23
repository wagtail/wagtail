apt-get update \
    && apt-get install -y locales \
    && rm -rf /var/lib/apt/lists/* \

echo "en_GB.UTF-8 UTF-8" >> /etc/locale.gen

locale-gen
