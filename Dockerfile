FROM ubuntu:22.04

# NOTE: This is an example Dockerfile for getting Indigo running in a simple way.
#       In production, you will probably want to use this as a template and make
#       your own changes.
#
#       For example, you probably want to use gunicorn to host the Django app,
#       rather than the built-in Django server.

# Install some necessary dependencies.
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y wget git \
  # python
  python3 python3-pip libpq-dev python-is-python3 \
  # pdftotext and ps2pdf
  poppler-utils ghostscript \
  # for fop
  default-jre

# Download and install FOP
RUN wget -q -O fop.tgz 'http://www.apache.org/dyn/closer.cgi?filename=/xmlgraphics/fop/binaries/fop-2.4-bin.tar.gz&action=download' && \
    tar zxf fop.tgz && \
    rm -f fop.tgz && \
    mv fop-2.4 /usr/local/share

ENV PATH=/usr/local/share/fop-2.4/fop:$PATH

# node
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs
# install sass for compiling assets before deploying
RUN npm i -g sass

WORKDIR /app

# install runtime node dependencies
# copying this in first means Docker can cache this operation
COPY package*.json /app/
RUN npm ci --no-audit --ignore-scripts --omit=dev

# Bring pip up to date; pip <= 22 (the default on ubuntu 22.04) is not supported
RUN pip install --upgrade pip

# These are production-only dependencies
RUN pip install psycopg2==2.9.9

# Copy the code
COPY . /app

# Install python requirements
RUN pip install -e .

# Compile static assets.
RUN python manage.py compilescss
# Note that we ignore 'docs' directories because some components have badly formed docs CSS.
RUN python manage.py collectstatic --noinput -i docs -i \*.scss 2>&1

CMD python manage.py
