FROM ubuntu:20.04

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

# dart sass
RUN wget -q -O dart-sass.tgz 'https://github.com/sass/dart-sass/releases/download/1.53.0/dart-sass-1.53.0-linux-x64.tar.gz' && \
  tar xzf dart-sass.tgz && \
  mv dart-sass/sass /usr/local/bin && \
  rm -rf dart-sass*

WORKDIR /app

# These are production-only dependencies
RUN pip install psycopg2==2.8.6

# Copy the code
COPY . /app

# Install python requirements
RUN pip install -e .

# Compile static assets.
#
# Note that we ignore 'docs' directories because some components
# have badly formed docs CSS.
RUN python manage.py compilescss && \
    python manage.py collectstatic --noinput -i docs -i \*.scss 2>&1

CMD python manage.py
