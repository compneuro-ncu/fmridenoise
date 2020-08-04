from typing import Tuple, List, Union
import numpy as np


def array_2d_row_identity(array: np.ndarray) -> Union[bool, List[Tuple[int, int]]]:
    # TODO: Make it more optimal, is it needed at all?
    """
    Checks whether any row of the numerical 2D array is identical with any other row.
    Args:
        array: input 2D array
    Returns: false if there are no identical rows in array or list of tuples with indexes of identical rows
    """
    if len(array.shape) != 2:
        raise ValueError(f"Input argument is not a two dimensional array but array with shape {array.shape}")
    identical = []
    total_rows = array.shape[0]
    for a in range(total_rows):
        for b in range(a+1, total_rows):
            if array[a].dtype != array[b].dtype:
                continue
            if np.allclose(array[a], array[b], rtol=1e-05, atol=1e-08):
                identical.append((a, b))
    return False if len(identical) == 0 else identical


def check_symmetry(matrix):
    """Checks if matrix is symmetrical."""
    return np.allclose(matrix, matrix.T, rtol=1e-05, atol=1e-08)