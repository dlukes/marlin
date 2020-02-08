############################### STAGE  1 ###############################

FROM python:2.7-alpine3.11 as stage1

ARG manatee_url=https://corpora.fi.muni.cz/noske/src/manatee-open/manatee-open-2.167.8.tar.gz

RUN apk add --no-cache \
  bison \
  build-base \
  curl \
  icu-dev \
  libtool \
  libxslt-dev \
  pcre-dev \
  swig

# Manatee
RUN curl -sLo manatee.tgz $manatee_url && \
  tar xzf manatee.tgz
RUN mv manatee-open-* manatee
WORKDIR /manatee
RUN ./configure --with-pcre PYTHON=/usr/local/bin/python && \
  make && \
  make DESTDIR=/tmp install

RUN cd /tmp && curl -sL --remote-name \
  https://cdnjs.cloudflare.com/ajax/libs/turbolinks/1.3.0/turbolinks.js

############################### STAGE  2 ###############################

FROM python:2.7-alpine3.11

COPY --from=stage1 /tmp/usr /usr
COPY --from=stage1 /tmp/turbolinks.js /opt/marlin/static/js/vendor/
RUN apk add --no-cache \
  bash \
  libgcc \
  libltdl \
  libstdc++ \
  pcre
COPY requirements.txt /
RUN pip install -r requirements.txt

COPY test /corpora/registry/
COPY vertikala /corpora/src/test
RUN encodevert -c test
COPY . /opt/marlin

ENTRYPOINT ["python", "/opt/marlin/marlin.py"]
