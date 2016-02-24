FROM ruby:2.2

ADD gen_locale.sh /gen_locale.sh
RUN bash /gen_locale.sh
ENV LANG=en_GB.UTF-8

# Install scss-lint
RUN gem install scss-lint
