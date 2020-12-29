#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
sphinx-apidoc -P -o ./source/apidoc --no-toc ../fmridenoise
make html