import unittest as ut
from fmridenoise.interfaces.quality_measures import QualityMeasures
import pandas as pd
import numpy as np


class QualityMeasuresTestCase(ut.TestCase):

    def setUp(self) -> None:
        self.group_conf_summary = pd.DataFrame(np.array([['m03', 'task', 0.1034750870617284, 1.1646298000000002, 50,
        True, 18, 2.4657534246575343],
       ['m04', 'task', 0.09806451376598077, 0.794708, 33, True, 1,
        0.136986301369863],
       ['m05', 'task', 0.06123372759303155, 0.14662384, 32, True, 0,
        0.0]], dtype=object), columns=['subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include', 'n_spikes',
       'perc_spikes'])
        self.distance_matrix = np.arange(16).reshape((4, 4))  # small fake distance matrix
        self.distance_matrix += self.distance_matrix.T
        self.distance_matrix -= np.diag(self.distance_matrix.diagonal())
        self.group_corr_mat = np.array([
            self.distance_matrix,
            [
                [0, 1, 1, 1],
                [1, 0, 1, 1],
                [1, 1, 0, 1],
                [1, 1, 1, 0]
            ],
            [
                [],
                [],
                [],
                []
            ],
        ])

