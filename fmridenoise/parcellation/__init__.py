import glob
from os.path import dirname, join


def get_parcellation_file_path(space: str) -> str:
    spaces = glob.glob(join(dirname(__file__), "*.nii.gz"))
    spaces = [path for path in spaces if space in path]
    if len(spaces) == 0:
        raise ValueError(f"Space file not found for argument: {space}")
    elif len(spaces) > 1:
        raise ValueError(f"Unexpected number of parcelation files ({len(spaces)}) found. Expected single file. ")
    return spaces[0]


def get_distance_matrix_file_path() -> str:
    ret = glob.glob(join(dirname(__file__), "*.npy"))
    if len(ret) != 1:
        raise ValueError(f"Unexpected number of parcelation files ({len(ret)}) found. Expected single file.")
    return ret[0]