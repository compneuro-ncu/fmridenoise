#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 10
rm -r ./dist
rm -r ./build
python setup.py sdist bdist_wheel || exit 13