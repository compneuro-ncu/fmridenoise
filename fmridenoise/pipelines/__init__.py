import glob
import os

def get_pipeline_path(name: str) -> str:
    dirname = os.path.dirname(__file__)
    path = os.path.join(dirname, name, ".json")
    if os.path.exists(path):
        return path
        

def get_pipelines_paths(names: set = None) -> set:
    dirname = os.path.dirname(__file__)
    if names is None:
        return set(glob.glob(os.path.join(dirname, "*.json")))
    elif names is not None and names <= get_pipelines_names():
        return set(map(lambda x: os.path.join(dirname, x, ".json"), names))
    else:
        raise ValueError("Unknown pipelines names: " + str(names))

def get_pipelines_names() -> set:
    return set(map(lambda x: os.path.basename(x).split(".")[0], get_pipelines_paths()))

def is_valid(name: str) -> bool:
    return True if name in get_pipelines_names() else False

