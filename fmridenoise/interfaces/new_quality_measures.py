import warnings

from nilearn.connectome import sym_matrix_to_vec
from nipype.interfaces.base import BaseInterfaceInputSpec, TraitedSpec, SimpleInterface
from nipype.interfaces.base import File, traits
import pandas as pd
import numpy as np
import typing as t
from scipy.stats import pearsonr
from fmridenoise.utils.numeric import check_symmetry, array_2d_row_identity
from fmridenoise.utils.plotting import make_motion_plot


class QualityMeasuresInputSpec(BaseInterfaceInputSpec):
    group_corr_mat = File(exists=True,
                          desc='Group connectivity matrix',
                          mandatory=True)

    group_conf_summary = File(exists=True,
                              desc='Group confounds summmary',
                              mandatory=True)

    distance_matrix = File(exists=True,
                           desc='Distance matrix',
                           mandatory=True)

    output_dir = File(desc='Output path')

    pipeline_name = traits.Str(mandatory=True)


class QualityMeasuresOutputSpec(TraitedSpec):
    fc_fd_summary = traits.List(
        exists=True,
        desc='QC-FC quality measures')

    edges_weight = traits.Dict(
        exists=True,
        desc='Weights of individual edges')

    edges_weight_clean = traits.Dict(
        exists=True,
        desc='Weights of individual edges after '
             'removing subjects with high motion')

    fc_fd_corr_values = traits.Dict(
        exists=True,
        desc='Pearson r values for correlation ' 
             'between FD and FC calculated for each edge')

    fc_fd_corr_values_clean = traits.Dict(
        exists=True,
        desc='Pearson r values for correlation ' 
             'between FD and FC calculated for each edge' 
             'after removing subjects with high motion')

    exclude_list = traits.List(
        exists=True,
        desc="List of subjects to exclude")


class QualityMeasures(SimpleInterface):

    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec

    sample_dict = {'All': True, 'No_high_motion': False}
    pval_tresh = 0.05

    @classmethod
    def _perc_fc_fd_uncorr(cls, fc_fd_pval: np.ndarray) -> float:
        return np.sum(fc_fd_pval < cls.pval_tresh) / len(fc_fd_pval) * 100

    @staticmethod
    def _distance_dependence(fc_fd_corr, distance_vector):
        return pearsonr(fc_fd_corr, distance_vector)[0]

    @staticmethod
    def calculate_fc_fd_correlations(group_conf_summary: pd.DataFrame,
                                     group_corr_vec: np.ndarray) -> t.Tuple[np.ndarray, np.ndarray]:
        assert not group_corr_vec.size == 0, "Empty arguments in calculate_fc_fd_correlations"
        n_edges = group_corr_vec.shape[1]
        fc_fd_corr, fc_fd_pval = np.zeros(n_edges), np.zeros(n_edges)
        fd = group_conf_summary['mean_fd'].values
        for i in range(n_edges):
            fc = group_corr_vec[:, i]
            corr = pearsonr(x=fc, y=fd)
            fc_fd_corr[i], fc_fd_pval[i] = corr

        if np.isnan(fc_fd_corr).any():
            fc_fd_corr = np.nan_to_num(fc_fd_corr)
            warnings.warn('NaN values in correlation measues; ' +
                          'replaced with zeros.')
        return fc_fd_corr, fc_fd_pval

    @classmethod
    def _quality_measure(cls,
                         group_conf_summary: pd.DataFrame,
                         distance_vec: np.ndarray,
                         group_corr_vec: np.ndarray,
                         all_subjects: bool):
        if all_subjects:
            group_conf_subsummary = group_conf_summary
            group_corr_subvec = group_corr_vec
        else:
            group_conf_subsummary = group_conf_summary[group_conf_summary['include'] == True] # TODO: Check case where all subjects are high motion
            group_corr_subvec = group_corr_vec[group_conf_summary['include'].values.astype(bool), :]
        fc_fd_corr, fc_fd_pval = cls.calculate_fc_fd_correlations(group_conf_subsummary, group_corr_subvec)
        summary = {'perc_fc_fd_uncorr': cls._perc_fc_fd_uncorr(fc_fd_pval),
                   'median_pearson_fc_fd': np.median(fc_fd_corr),
                   'distance_dependence': cls._distance_dependence(fc_fd_corr, distance_vec),
                   'tdof_loss': group_conf_subsummary['n_conf'].mean(),
                   'n_subjects': len(group_conf_summary),
                   'n_excluded': len(group_conf_summary) - len(group_conf_subsummary),
                   'all': all_subjects,
                   }
        edges_weight = group_corr_subvec.mean(axis=0)
        excluded_subjects = group_conf_summary[group_conf_summary['include'] == False]['subject']
        return summary, edges_weight, excluded_subjects, group_corr_subvec

    @classmethod
    def calculate_quality_measures(
        cls,
        group_conf_summary: pd.DataFrame,
        group_corr_mat: np.ndarray,
        distance_matrix: np.ndarray) -> t.Tuple[t.List[dict], np.ndarray, np.ndarray, t.List[str]]:
        quality_measures = []
        excluded_subjects_names = set()
        edges_weights = []
        group_corr_vec = sym_matrix_to_vec(group_corr_mat)
        distance_vec = sym_matrix_to_vec(distance_matrix)
        for sample, all_subjects in cls.sample_dict.items():
            summary, edges_weight, excluded_subjects, fc_fd_corr_vector = cls._quality_measure(group_conf_summary, distance_vec,
                                                                            group_corr_vec, all_subjects)
            excluded_subjects_names |= set(excluded_subjects)
            quality_measures.append(summary)

            if all_subjects:
                edges_weight = edges_dict

            else:
                edges_weight_clean = edges_dict

            edges_weights.append(edges_weight)
        return quality_measures, edges_weights[0], edges_weights[1], list(excluded_subjects_names)

    @staticmethod
    def validate_group_conf_summary(group_conf_summary: pd.DataFrame) -> None:
        # TODO: Check 'include' - what should happen if only one participant is not high motion
        # TODO: or all participants are high motion (is there even possible?)
        # TODO: Hint - interface collapse when either of cases are present (during correlations calc, look at tests)
        """
        Checks if correct summary data are provided.
        Raises exceptions when data is not valid.
        Each row should contain data for one subject.
        """

        # Checks if file have data inside
        if group_conf_summary.empty:
            raise ValueError('Missing confounds summary data (empty dataframe)')
            # Checks if data frame contains proper columns
            # confounds_fields - from confound output definition
            all_possible_fields = {'subject', 'task', 'session', 'mean_fd', 'max_fd', 'n_conf', 'include', 'n_spikes',
                                   'perc_spikes'}
            mandatory_fields = {'subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include'}
            provided_fields = set(group_conf_summary.columns)
            excess_fields = provided_fields - all_possible_fields
            mandatory_provided = provided_fields >= mandatory_fields
            if not mandatory_provided:
                raise ValueError(f'Confounds file require to have columns of\n{mandatory_fields}\n'
                                 f'but data frame contains only columns of\n{group_conf_summary.columns}')
            if len(excess_fields) > 0:
                raise ValueError(f"Confounds file has excess fields {excess_fields}, check input dataframe")

            # Check if number of subjects corresponds to data frame size
            if len(group_conf_summary) != len(np.unique(group_conf_summary['subject'])):
                raise ValueError('Each subject should have only one ' +
                                 'corresponding summary values.')

            # Check if summary contains data from a one task
            if len(np.unique(group_conf_summary['task'])) > 1:
                raise ValueError('Summary confouds data should contain ' +
                                 'data from a one task at time.')

            # Check if subjects' numerical data are not idenical
            num_data_columns = {'mean_fd', 'max_fd', 'n_conf', 'n_spikes', 'perc_spikes'}
            result = array_2d_row_identity(group_conf_summary[provided_fields & num_data_columns].values)
            if result is not False:
                raise ValueError('Confounds summary data of some subjects are identical')

            # Check if number of subject allows to calculate summary measures
            if len(group_conf_summary['subject']) < 10:
                warnings.warn('Quality measures may be not meaningful ' +
                              'for small (lesser than 10) sample sizes.')  # TODO: Maybe push all messages like this to interface output and present it in final raport?

    @staticmethod
    def validate_fc_matrices(group_corr_matrix: np.ndarray, group_conf_summary: pd.DataFrame) -> None:
        for matrix in group_corr_matrix:
            if not check_symmetry(matrix):
                raise ValueError('Correlation matrix is not symmetrical.')

            # Check if subjects' data are not identical
        # TODO: Reimplement row check in more efficient way (why do we check this???)
        # if array_2d_row_identity(group_corr_matrix) is not False:
        #     raise ValueError('Connectivity values of some subjects ' +
        #                      'are identical.')
        # Check if a number of FC matrices is the same as the number
        # of subjects
        if len(group_corr_matrix) != len(group_conf_summary):
            raise ValueError('Number of FC matrices does not correspond ' +
                             'to the number of confound summaries.')

    def _run_interface(self, runtime):
        # TODO: Validation, consider removing or checking other data properties
        group_conf_summary_df = pd.read_csv(self.inputs.group_conf_summary, sep='\t', header=0)
        group_corr_mat_arr = np.load(self.inputs.group_corr_mat)
        distance_matrix_arr = np.load(self.inputs.distance_matrix)
        self.validate_group_conf_summary(group_conf_summary_df)
        self.validate_fc_matrices(group_corr_mat_arr, group_conf_summary_df)
        summaries, edges_weight, edges_weight_clean, exclude_list = self.calculate_quality_measures(
            group_conf_summary_df,
            group_corr_mat_arr,
            distance_matrix_arr
        )

        for summary in summaries:
            summary['pipeline'] = self.inputs.pipeline_name
        edges_weight = {self.inputs.pipeline_name: edges_weight}
        edges_weight_clean = {self.inputs.pipeline_name: edges_weight_clean}
        make_motion_plot(group_conf_summary_df, self.inputs.pipeline_name, self.inputs.output_dir)
        self._results['fc_fd_summary'] = summaries
        self._results['edges_weight'] = edges_weight
        self._results['edges_weight_clean'] = edges_weight_clean
        self._results['exclude_list'] = exclude_list
        return runtime
