import glob
import os
from fmridenoise.utils.utils import cast_bool, swap_booleans
from os.path import  exists
import json

def get_pipeline_path(name: str) -> str:
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, name) + ".json"
    if os.path.exists(path):
        return path
    else:
        raise ValueError(f"File '{path}' is not part of fmridenoise valid pipelines!")

def get_pipeline_name(path: str) -> str:
    dirname = os.path.dirname(__file__)
    if os.path.dirname(path) != dirname or not os.path.exists(path):
        raise ValueError(f"File {path} is not a pipeline from fmridenoise ({dirname})")
    return os.path.basename(path).split(".")[0]


def get_pipelines_paths(names: set = None) -> set:
    dirname = os.path.dirname(__file__)
    if names is None:
        return set(glob.glob(os.path.join(dirname, "*.json")))
    elif names is not None and names <= get_pipelines_names():
        return set(map(get_pipeline_path, names))
    else:
        raise ValueError("Unknown pipelines names: " + str(names))


def get_pipelines_names() -> set:
    return set(map(get_pipeline_name , get_pipelines_paths()))


def is_valid_name(name: str) -> bool:
    return True if name in get_pipelines_names() else False

def is_IcaAROMA(pipeline: dict) -> bool:
    return cast_bool(pipeline["aroma"])

def load_pipeline_from_json(json_path: str) -> dict:
    """
    Loads json file and prepares it for further use (e.g. assures proper types interpretation)
    :param json_path: path to json file
    :return: jsonlike dictionary
    """
    if not exists(json_path):
        raise IOError(f"File '{json_path}' does not exists!")
    with open(json_path, 'r') as json_file:
        js = json.load(json_file)
    js = swap_booleans(js, inplace=True)
    return js