#!/usr/bin/env bash

set -e

echo "Extracting translatable strings from django"
for d in indigo indigo_api indigo_app indigo_social indigo_za; do
  pushd $d
  django-admin makemessages -a --no-wrap
  popd
done
