from fmridenoise.utils.numeric import array_2d_row_identity
import unittest as ut
import numpy as np


class ArrayRowIdentityTestCae(ut.TestCase):

    def test_on_array_with_identical_rows(self):
        array = np.reshape(np.arange(12), (4, 3))
        array[0] = [1, 1, 1]
        array[2] = [1, 1, 1]
        result = array_2d_row_identity(array)
        self.assertEqual(1, len(result))
        self.assertEqual((0, 2), result[0])

    def test_on_array_without_identical_rows(self):
        array = np.reshape(np.arange(12), (4, 3))
        result = array_2d_row_identity(array)
        self.assertFalse(result)

    def test_on_invalid_array(self):
        flat = np.arange(12)
        d3_array = np.reshape(flat, (2, 2, 3))
        with self.assertRaises(ValueError):
            result = array_2d_row_identity(flat)
        with self.assertRaises(ValueError):
            result = array_2d_row_identity(d3_array)
