import glob
from os.path import dirname, join

def get_parcelation_file_path() -> str:
    ret = glob.glob(join(dirname(__file__), "*.nii.gz"))
    if len(ret) != 1:
        raise ValueError("Unexpected number of parcelation files")
    return ret[0]

def get_distance_matrix_file_path() -> str:
    ret = glob.glob(join(dirname(__file__), "*.npy"))
    if len(ret) != 1:
        raise ValueError("Unexpected number of parcelation files")
    return ret[0]