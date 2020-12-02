import numpy as np


def check_symmetry(matrix):
    """Checks if matrix is symmetrical."""
    return np.allclose(matrix, matrix.T, rtol=1e-05, atol=1e-08)