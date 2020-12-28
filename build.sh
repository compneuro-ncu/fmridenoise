#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 10
rm -r ./dist
rm -r ./build
python setup.py sdist bdist_wheel || exit 13
echo "Do you want to install package? (y|Y to install)"
read answer
if [[ "$answer" == "y"  || "$answer" == "Y" ]]
then
pip install "$(ls ./dist/*.whl)"
fi
