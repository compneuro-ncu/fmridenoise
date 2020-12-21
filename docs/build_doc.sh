#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
PYTHONPATH=$PYTHONPATH:$(dirname "$PWD")
export PYTHONPATH
sphinx-apidoc -P -o ./source/apidoc --no-toc ../fmridenoise
make html