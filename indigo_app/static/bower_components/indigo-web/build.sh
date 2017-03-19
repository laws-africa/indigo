#!/bin/bash
set -e
set -x

sass --style compressed scss/akoma-ntoso.scss css/akoma-ntoso.min.css
sass scss/akoma-ntoso.scss css/akoma-ntoso.css
