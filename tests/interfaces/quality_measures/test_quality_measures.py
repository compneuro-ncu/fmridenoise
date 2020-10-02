import unittest as ut
from fmridenoise.interfaces.quality_measures import QualityMeasures
import pandas as pd
import numpy as np
from nipype import Node
import tempfile
import shutil
from os.path import join
from numpy.testing import assert_array_equal, assert_array_almost_equal
from fmridenoise.pipelines import load_pipeline_from_json, get_pipeline_path


class QualityMeasuresAsNodeTestCase(ut.TestCase):
    group_conf_summary = pd.DataFrame(np.array([['m03', 'task', 0.1034750870617284, 1.1646298000000002, 50,
                                                      True, 18, 2.4657534246575343],
                                                     ['m04', 'task', 0.09806451376598077, 0.794708, 33, False, 1,
                                                      0.136986301369863],
                                                     ['m05', 'task', 0.06123372759303155, 0.14662384, 32, True, 0,
                                                      0.0]], dtype=object),
                                      columns=['subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include',
                                               'n_spikes', 'perc_spikes'])
    distance_matrix = np.array([[0, 1, 2, 3],
                                [1, 0, 4, 5],
                                [2, 4, 0, 6],
                                [3, 5, 6, 0]])
    group_corr_mat = np.array([
        distance_matrix,  # one input is distance matrix
        [  # trivial input
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ],
        [  # >normal< input
            [0, 5, 8, 1],
            [5, 0, 7, 9],
            [8, 7, 0, 3],
            [1, 9, 3, 0]
        ],
    ])
    pipeline = load_pipeline_from_json(get_pipeline_path('pipeline-Null'))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tempdir)

    @classmethod
    def setUpClass(cls) -> None:
        cls.tempdir = tempfile.mkdtemp()
        group_conf_summary_file = join(cls.tempdir, 'group_conf_summary.tsv')
        cls.group_conf_summary.to_csv(group_conf_summary_file, sep="\t", index=False)
        distance_matrix_file = join(cls.tempdir, "distance_matrix.npy")
        np.save(distance_matrix_file, cls.distance_matrix)
        group_corr_mat_file = join(cls.tempdir, "group_corr_mat.npy")
        np.save(group_corr_mat_file, cls.group_corr_mat)
        cls.quality_measures_node = Node(QualityMeasures(), name="QualityMeasures")
        cls.quality_measures_node.inputs.group_conf_summary = group_conf_summary_file
        cls.quality_measures_node.inputs.distance_matrix = distance_matrix_file
        cls.quality_measures_node.inputs.group_corr_mat = group_corr_mat_file
        cls.quality_measures_node.inputs.pipeline = cls.pipeline
        cls.quality_measures_node.inputs.output_dir = cls.tempdir
        cls.result = cls.quality_measures_node.run()

    def test_summary_output(self) -> None:
        tested = self.result.outputs.fc_fd_summary
        self.assertEqual(2, len(tested))
        self.assertIsInstance(self.result.outputs.fc_fd_summary[0], dict)
        first: dict = tested[0]
        second: dict = tested[1]
        self.assertEqual(second.keys(), first.keys())
        self.assertEqual(set(first.keys()), {'pipeline', 'median_pearson_fc_fd', 'perc_fc_fd_uncorr', 'distance_dependence',
                                             'tdof_loss', 'n_subjects', 'n_excluded', 'all'})
        # values checks for first summary (all subjects)
        self.assertEqual(3, first['n_subjects'])
        self.assertEqual(0, first['n_excluded'])
        self.assertEqual((50 + 33 + 32) / 3, first['tdof_loss'])
        self.assertTrue(first['all'])

        # values checks for second summary (no high motion)
        self.assertEqual(3, second['n_subjects'])
        self.assertEqual(1, second['n_excluded'])
        self.assertEqual((50 + 32) / 2, second['tdof_loss'])
        self.assertFalse(second['all'])

    def test_excluded_output(self) -> None:
        self.assertEqual(1, len(self.result.outputs.exclude_list))
        self.assertEqual(['m04'], self.result.outputs.exclude_list)

    def test_edges_weight(self):
        edges_weight: dict = self.result.outputs.edges_weight
        self.assertIsInstance(edges_weight, dict)
        self.assertTrue(all(isinstance(key, str) for key in edges_weight.keys()))
        self.assertTrue(all(isinstance(value, np.ndarray) for value in edges_weight.values()))

        # value check
        from nilearn.connectome import sym_matrix_to_vec
        vec: np.ndarray = sym_matrix_to_vec(self.group_corr_mat)
        tested_edges_weight = vec.mean(axis=0)
        assert_array_equal(edges_weight[self.pipeline['name']], tested_edges_weight)

    def test_edges_weight_clean(self):
        edges_weight: dict = self.result.outputs.edges_weight_clean
        self.assertIsInstance(edges_weight, dict)
        self.assertTrue(all(isinstance(key, str) for key in edges_weight.keys()))
        self.assertTrue(all(isinstance(value, np.ndarray) for value in edges_weight.values()))

        # value check
        from nilearn.connectome import sym_matrix_to_vec
        group_corr_mat = self.group_corr_mat[[0, 2], :, :]
        vec: np.ndarray = sym_matrix_to_vec(group_corr_mat)
        tested_edges_weight = vec.mean(axis=0)
        assert_array_equal(edges_weight[self.pipeline['name']], tested_edges_weight)

    def test_fc_fd_vec(self):
        corr_vec: dict = self.result.outputs.fc_fd_corr_values
        self.assertIsInstance(corr_vec, dict)
        self.assertTrue(all(isinstance(key, str) for key in corr_vec.keys()))
        self.assertTrue(all(isinstance(value, np.ndarray) for value in corr_vec.values()))

        # value check
        from nilearn.connectome import sym_matrix_to_vec
        vec = sym_matrix_to_vec(self.group_corr_mat)
        corr, _ = QualityMeasures.calculate_fc_fd_correlations(self.group_conf_summary, vec)  # TODO: Replace method call
        assert_array_almost_equal(corr_vec[self.pipeline['name']], corr)

    def test_fc_fd_vec_clean(self):
        corr_vec: dict = self.result.outputs.fc_fd_corr_values_clean
        self.assertIsInstance(corr_vec, dict)
        self.assertTrue(all(isinstance(key, str) for key in corr_vec.keys()))
        self.assertTrue(all(isinstance(value, np.ndarray) for value in corr_vec.values()))

        # value check
        from nilearn.connectome import sym_matrix_to_vec
        group_corr_mat = self.group_corr_mat[[0, 2], :, :]
        vec: np.ndarray = sym_matrix_to_vec(group_corr_mat)
        corr, _ = QualityMeasures.calculate_fc_fd_correlations(
            self.group_conf_summary[self.group_conf_summary['include'] == True], vec)
        assert_array_almost_equal(corr_vec[self.pipeline['name']], corr)


# TODO: Check this tests
@ut.skip
class QualityMeasuresEdgeCases(ut.TestCase):
    
    def test_only_high_motion(self):  # TODO: Handle the case
        group_conf_summary = pd.DataFrame(np.array([['m03', 'task', 0.1034750870617284, 1.1646298000000002, 50,
                                                     False, 18, 2.4657534246575343],
                                                    ['m04', 'task', 0.09806451376598077, 0.794708, 33, False, 1,
                                                     0.136986301369863],
                                                    ['m05', 'task', 0.06123372759303155, 0.14662384, 32, False, 0,
                                                     0.0]], dtype=object),
                                          columns=['subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include',
                                                   'n_spikes', 'perc_spikes'])
        distance_matrix = np.array([[0, 1, 2, 3],
                                    [1, 0, 4, 5],
                                    [2, 4, 0, 6],
                                    [3, 5, 6, 0]])
        group_corr_mat = np.array([
            distance_matrix,  # one input is distance matrix
            [  # trivial input
                [0, 1, 1, 1],
                [1, 0, 1, 1],
                [1, 1, 0, 1],
                [1, 1, 1, 0]
            ],
            [  # >normal< input
                [0, 5, 8, 1],
                [5, 0, 7, 9],
                [8, 7, 0, 3],
                [1, 9, 3, 0]
            ],
        ])
        # TODO: What is supposed to be there?
        QualityMeasures.validate_group_conf_summary(group_conf_summary)
        QualityMeasures.validate_fc_matrices(group_corr_mat, group_conf_summary)
        QualityMeasures.calculate_quality_measures(group_conf_summary, group_corr_mat, distance_matrix)
        # TODO: Further tests after resolving initial exception hell

    def test_single_no_high_motion(self):
        group_conf_summary = pd.DataFrame(np.array([['m03', 'task', 0.1034750870617284, 1.1646298000000002, 50,
                                                     True, 18, 2.4657534246575343],
                                                    ['m04', 'task', 0.09806451376598077, 0.794708, 33, False, 1,
                                                     0.136986301369863],
                                                    ['m05', 'task', 0.06123372759303155, 0.14662384, 32, False, 0,
                                                     0.0]], dtype=object),
                                          columns=['subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include',
                                                   'n_spikes', 'perc_spikes'])
        distance_matrix = np.array([[0, 1, 2, 3],
                                    [1, 0, 4, 5],
                                    [2, 4, 0, 6],
                                    [3, 5, 6, 0]])
        group_corr_mat = np.array([
            distance_matrix,  # one input is distance matrix
            [  # trivial input
                [0, 1, 1, 1],
                [1, 0, 1, 1],
                [1, 1, 0, 1],
                [1, 1, 1, 0]
            ],
            [  # >normal< input
                [0, 5, 8, 1],
                [5, 0, 7, 9],
                [8, 7, 0, 3],
                [1, 9, 3, 0]
            ],
        ])
        # TODO: What is supposed to be there?
        QualityMeasures.validate_group_conf_summary(group_conf_summary)
        QualityMeasures.validate_fc_matrices(group_corr_mat, group_conf_summary)
        QualityMeasures.calculate_quality_measures(group_conf_summary, group_corr_mat, distance_matrix)
        # TODO: Further tests after resolving initial exception hell
