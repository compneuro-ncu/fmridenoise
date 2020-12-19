cd "$(dirname "$0")" || exit 1
PYTHONPATH=$PYTHONPATH:$(dirname "$PWD")
export PYTHONPATH
make html