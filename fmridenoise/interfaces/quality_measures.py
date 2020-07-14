from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    File,
    traits
)

import numpy as np
import pandas as pd
from nilearn.connectome import sym_matrix_to_vec
from scipy.stats import pearsonr
from os.path import join
from itertools import chain
import warnings
from fmridenoise.utils.plotting import make_motion_plot, make_kdeplot, make_catplot
from fmridenoise.utils.numeric import array_2d_row_identity, check_symmetry


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

    exclude_list = traits.List(
        exists=True,
        desc="List of subjects to exclude")


class QualityMeasures(SimpleInterface):
    """Calculates quality measures based on confound summary and connectivity matrices."""

    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edges_weights = {}
        self.edges_weights_clean = {}
        self.sample_dict = {'All': True, 'No_high_motion': False}
        self.group_conf_summary_df: pd.DataFrame = ...  # initialized in _run_interface
        self.group_corr_mat_arr: np.ndarray = ...  # initialized in _run_interface
        self.distance_matrix_arr: np.ndarray = ...  # initialized in _run_interface

    def _validate_group_conf_summary(self):
        """Checks if correct summary data are provided.
        Each row should contain data for one subject."""

        # Checks if file have data inside
        if self.group_conf_summary_df.empty:
            raise ValueError('Missing confounds summary data (empty dataframe)')
        # Checks if data frame contains proper columns
        # confounds_fields - from confound output definition
        confounds_fields = ['subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include', 'n_spikes', 'perc_spikes']
        if any(field not in self.group_conf_summary_df.columns for field in confounds_fields):
            raise ValueError(f'Confounds file require to have columns of\n{confounds_fields}\n'
                             f'but data frame contains only columns of\n{self.group_conf_summary_df.columns}')

        # Check if number of subjects corresponds to data frame size
        if len(self.group_conf_summary_df) != len(np.unique(self.group_conf_summary_df['subject'])):
            raise ValueError('Each subject should have only one ' +
                             'corresponding summary values.')

        # Check if summary contains data from a one task
        if len(np.unique(self.group_conf_summary_df['task'])) > 1:
            raise ValueError('Summary confouds data should contain ' +
                             'data from a one task at time.')

        # Check if subjects' numerical data are not idenical
        num_data_columns = ['mean_fd', 'max_fd', 'n_conf', 'n_spikes', 'perc_spikes']
        result = array_2d_row_identity(self.group_conf_summary_df[num_data_columns].values)
        if result is not False:
            raise ValueError('Confounds summary data of some subjects are identical')

        # Check if number of subject allows to calculate summary measures
        if len(self.group_conf_summary_df['subject']) < 10:
            warnings.warn('Quality measures may be not meaningful ' +
                          'for small (lesser than 10) sample sizes.')  # TODO: Maybe push all messages like this to interface output and present it in final raport?

    def _validate_fc_matrices(self):  # NOTE: A bit of anti-patter. Name of method - validate something.
                                      #       Does not corespond to it's functionality which validades value
                                      #       AND assigns new object variable.
        """Checks if correct FC matrices are provided."""

        # Check if each matrix is symmetrical
        for matrix in self.group_corr_mat_arr:
            if not check_symmetry(matrix):
                raise ValueError('Correlation matrix is not symmetrical.')

        self.group_corr_vec = sym_matrix_to_vec(self.group_corr_mat_arr)  # FIX: why completly new variable is created in validation method

        # Check if subjects' data are not idenical
        if array_2d_row_identity(self.group_corr_vec):
            raise ValueError('Connectivity values of some subjects ' +
                             'are identical.')

        # Check if a number of FC matrices is the same as the nymber
        # of subjects
        if len(self.group_corr_vec) != len(self.group_conf_summary_df):
            raise ValueError('Number of FC matrices does not correspond ' +
                             'to the number of confound summaries.')

    def _validate_distance_matrix(self):
        """Validates distance matrix."""

        # Check if distance matrix has the same shape as FC matrix
        if self.group_corr_mat_arr[0].shape != self.distance_matrix_arr.shape:
            raise ValueError(f'FC matrices have shape {self.group_corr_mat_arr.shape} ' +
                             f'while distance matrix {self.distance_matrix_arr.shape}')

        self.distance_vector = sym_matrix_to_vec(self.distance_matrix_arr)  # FIX: same as above, function naming convention

    @property
    def n_subjects(self):
        """Returns total number of subjects."""
        return len(self.group_conf_summary_df)

    @property
    def subjects_list(self):
        """Returns list of all subjects."""
        return [f"sub-{sub}" for sub in self.group_conf_summary_df['subject']]

    def _get_subject_filter(self, all_subjects=True) -> np.ndarray:
        """Returns filter vector with subjects included in analysis."""
        if all_subjects:
            return np.ones(self.n_subjects, dtype=bool)
        else:
            return self.group_conf_summary_df['include'].values.astype('bool')

    def _get_n_excluded(self, subjects_filter):
        """Gets lumber of excluded subjests."""
        self.n_excluded = self.n_subjects - sum(subjects_filter)

    def _get_excluded_subjects(self, subjects_filter):
        """Gets list of excluded subjects."""
        self.excluded_subjects = list(np.array(self.subjects_list)[[not i for i in subjects_filter]])

    def _get_fc_fd_correlations(self, subjects_filter):
        """Calculates correlations between edges weights and mean framewise displacement
        for all subjects."""
        n_edges = self.group_corr_vec.shape[1]
        fc_fd_corr, fc_fd_pval = (np.zeros(n_edges) for _ in range(2))

        for i in range(n_edges):
            fc = self.group_corr_vec[subjects_filter, i]
            fd = self.group_conf_summary_df['mean_fd'].values[subjects_filter]
            corr = pearsonr(x=fc, y=fd)
            fc_fd_corr[i], fc_fd_pval[i] = corr

            if np.isnan(fc_fd_corr).any():
                fc_fd_corr = np.nan_to_num(fc_fd_corr)
                warnings.warn('NaN values in correlation measues; ' +
                              'replaced with zeros.')

        self.fc_fd_corr = fc_fd_corr
        self.fc_fd_pval = fc_fd_pval

    def pearson_fc_fd_median(self):
        """Calculates median of FC-FD correlations."""
        return np.median(self.fc_fd_corr)

    def perc_fc_fd_uncorr(self):
        """Calculates percent of significant FC-FD correlations (uncorrected)."""
        return np.sum(self.fc_fd_pval < 0.05) / len(self.fc_fd_pval) * 100

    def distance_dependence(self):
        """Calculates distance dependence of FC-FD correlations."""
        return pearsonr(self.fc_fd_corr, self.distance_vector)[0]

    def dof_loss(self):
        """Calculates degrees of freedom loss."""
        return self.group_conf_summary_df['n_conf'].mean()

    def _get_mean_edges_dict(self, subject_filter):
        """Greates fictionary with mean edge weights for selected subject filter."""
        self.edges_dict = {self.inputs.pipeline_name: self.group_corr_vec[subject_filter].mean(axis=0)}

    def _create_summary_dict(self, all_subjects=None, n_excluded=None):
        """Generates dictionary with all summary measures."""
        return {'pipeline': self.inputs.pipeline_name,
                'perc_fc_fd_uncorr': self.perc_fc_fd_uncorr(),
                'pearson_fc_fd': self.pearson_fc_fd_median(),
                'distance_dependence': self.distance_dependence(),
                'tdof_loss': self.dof_loss(),
                'n_subjects': self.n_subjects,
                'n_excluded': n_excluded,
                'all': all_subjects,
                }

    def _quality_measures(self):
        """Iterates over subject filters to get summary measures."""
        quality_measures = []
        for key, value in self.sample_dict.items():
            subject_filter = self._get_subject_filter(all_subjects=value)
            self._get_n_excluded(subject_filter)
            self._get_excluded_subjects(subject_filter)
            self._get_fc_fd_correlations(subject_filter)
            summary = self._create_summary_dict(all_subjects=value, n_excluded=self.n_excluded)
            quality_measures.append(summary)
            self._get_mean_edges_dict(subject_filter)

            if value:
                self.edges_weight = self.edges_dict
            else:
                self.edges_weight_clean = self.edges_dict
        return quality_measures

    def _make_figures(self):
        """Generates figures."""
        make_motion_plot(self.group_conf_summary_df, self.inputs.pipeline_name, self.inputs.output_dir)

    def _run_interface(self, runtime):
        self.group_conf_summary_df = pd.read_csv(self.inputs.group_conf_summary, sep='\t', header=0)
        self.group_corr_mat_arr = np.load(self.inputs.group_corr_mat)
        self.distance_matrix_arr = np.load(self.inputs.distance_matrix)
        self._validate_group_conf_summary()
        self._validate_fc_matrices()
        self._validate_distance_matrix()
        quality_measures = self._quality_measures()
        self._make_figures()

        self._results['fc_fd_summary'] = quality_measures
        self._results['edges_weight'] = self.edges_weight
        self._results['edges_weight_clean'] = self.edges_weight_clean
        self._results['exclude_list'] = self.excluded_subjects

        return runtime


#  NOTE: check_identity and check_symmetry moved to fmridenoise.utils.numeric
#  NOTE: Function renamed to array_2d_row_identity
#  NOTE: Delete both check functions
def check_identity(matrix):  # FIX: This function does not calculates/checks what it's suppose to
    """Checks whether any row of the matrix is identical with any other row."""
    identical = []
    for a in range(len(matrix)):
        for b in range(a):
            identical.append(np.allclose(a, b, rtol=1e-05, atol=1e-08))
    return any(identical)


# def check_symmetry(matrix):
#     """Checks if matrix is symmetrical."""
#     return np.allclose(matrix, matrix.T, rtol=1e-05, atol=1e-08)

#  NOTE: Delete MegreGroupQualityMeasuresOutputSpec
# class MergeGroupQualityMeasuresOutputSpec(TraitedSpec):
#     fc_fd_summary = traits.List()
#     edges_weight = traits.List()
#     edges_weight_clean = traits.List()
#     exclude_list = traits.Set(traits.Str())
#
#
# class MergeGroupQualityMeasuresInputSpec(BaseInterfaceInputSpec):
#     fc_fd_summary = traits.List()
#     edges_weight = traits.List()
#     edges_weight_clean = traits.List()
#     exclude_list = traits.List(default=[])
#
#
# class MergeGroupQualityMeasures(SimpleInterface):
#     input_spec = MergeGroupQualityMeasuresInputSpec
#     output_spec = MergeGroupQualityMeasuresOutputSpec
#
#     def _run_interface(self, runtime):
#         self._results['fc_fd_summary'] = self.inputs.fc_fd_summary
#         self._results['edges_weight'] = self.inputs.edges_weight
#         self._results['edges_weight_clean'] = self.inputs.edges_weight_clean
#         self._results['exclude_list'] = set(chain(*chain(*self.inputs.exclude_list)))
#         return runtime


class PipelinesQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List(
        exists=True,
        desc="QC-FC quality measures")

    edges_weight = traits.Dict(
        exists=True,
        desc="Weights of individual edges")

    edges_weight_clean = traits.Dict(
        exists=True,
        desc="Mean weights of individual edges (no high motion)")

    output_dir = File(  # needed to save data in other directory
        desc="Output path")  # TODO: Implement temp dir


class PipelinesQualityMeasuresOutputSpec(TraitedSpec):
    pipelines_fc_fd_summary = File(
        exists=False,
        desc="Group QC-FC quality measures")

    pipelines_edges_weight = File(
        exists=False,
        desc="Group weights of individual edges")

    pipelines_edges_weight_clean = File(
        exists=False,
        desc="Group weights of individual edges")

    plot_pipeline_edges_density = File(
        exists=False,
        desc="Density of edge weights (all subjects)"
    )

    plot_pipelines_edges_density_no_high_motion = File(
        exist=False,
        desc="Density of edge weights (no high motion)"
    )

    plot_pipelines_fc_fd_pearson = File(
        exist=False
    )

    plot_pipelines_fc_fd_uncorr = File(
        exist=False
    )

    plot_pipelines_distance_dependence = File(
        exist=False
    )

    plot_pipelines_tdof_loss = File(
        exist=False
    )


class PipelinesQualityMeasures(SimpleInterface):
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec

    def _get_pipeline_summaries(self):
        """Gets and saves table with quality measures for each pipeline"""
        self.pipelines_fc_fd_summary = pd.DataFrame()

        for pipeline in self.inputs.fc_fd_summary:
            self.pipelines_fc_fd_summary = pd.concat([self.pipelines_fc_fd_summary,
                                                      pd.DataFrame(pipeline, index=[0])],
                                                     axis=0)

        self.fname1 = join(self.inputs.output_dir, f"pipelines_fc_fd_summary.tsv")
        self.pipelines_fc_fd_summary.to_csv(self.fname1, sep='\t', index=False)

    def _get_pipelines_edges_weight(self):
        """Gets and saves tables with mean edges weights for raw and cleaned data"""
        self.pipelines_edges_weight = pd.DataFrame()
        self.pipelines_edges_weight_clean = pd.DataFrame()

        for edges, edges_clean in zip(self.inputs.edges_weight, self.inputs.edges_weight_clean):
            self.pipelines_edges_weight = pd.concat([self.pipelines_edges_weight,
                                                     pd.DataFrame(self.inputs.edges_weight[edges],
                                                                  columns=[edges])],
                                                    axis=1)
            self.pipelines_edges_weight_clean = pd.concat([self.pipelines_edges_weight_clean,
                                                           pd.DataFrame(self.inputs.edges_weight[edges_clean],
                                                                        columns=[edges_clean])],
                                                          axis=1)
        self.fname2 = join(self.inputs.output_dir, f"pipelines_edges_weight.tsv")
        self.fname3 = join(self.inputs.output_dir, f"pipelines_edges_weight_clean.tsv")
        self.pipelines_edges_weight.to_csv(self.fname2, sep='\t', index=False)
        self.pipelines_edges_weight_clean.to_csv(self.fname3, sep='\t', index=False)

    def _make_summary_figures(self):
        """Makes summary figures for all quality mesures"""
        self.plot_pipelines_edges_density = make_kdeplot(data=pipelines_edges_weight,
                                                         title="Density of edge weights (all subjects)",
                                                         filename="pipelines_edges_density",
                                                         output_dir=self.inputs.output_dir)
        self.plot_pipelines_edges_density_clean = make_kdeplot(data=pipelines_edges_weight_clean,
                                                               title="Density of edge weights (no high motion)",
                                                               filename="pipelines_edges_density_no_high_motion",
                                                               output_dir=self.inputs.output_dir)
        self.plot_fc_fd_pearson = make_catplot(x="pearson_fc_fd",
                                               data=self.pipelines_fc_fd_summary,
                                               xlabel="QC-FC (Pearson's r)",
                                               filename="plot-fc_fd_pearson",
                                               output_dir=self.inputs.output_dir)
        self.perc_plot_fc_fd_uncorr = make_catplot(x="perc_fc_fd_uncorr",
                                                   data=self.pipelines_fc_fd_summary,
                                                   xlabel="QC-FC uncorrected (%)",
                                                   filename="plot-perc_fc_fd_uncorr",
                                                   output_dir=self.inputs.output_dir)
        self.plot_distance_dependence = make_catplot(x="distance_dependence",
                                                     data=self.pipelines_fc_fd_summary,
                                                     xlabel="Distance-dependence",
                                                     filename="plot-distance_dependence",
                                                     output_dir=self.inputs.output_dir)
        self.plot_tdof_loss = make_catplot(x="tdof_loss",
                                           data=self.pipelines_fc_fd_summary,
                                           xlabel="fDOF-loss",
                                           filename="plot-tdof_loss",
                                           output_dir=self.inputs.output_dir)

    def _run_interface(self, runtime):
        self._get_pipeline_summaries()
        self._get_pipelines_edges_weight()
        self._make_summary_figures()

        self._results['pipelines_fc_fd_summary'] = self.fname1
        self._results['pipelines_edges_weight'] = self.fname2
        self._results['pipelines_edges_weight_clean'] = self.fname3
        self._results['plot_pipeline_edges_density'] = self.plot_pipelines_edges_density
        self._results['plot_pipelines_edges_density_no_high_motion'] = self.plot_pipelines_edges_density_clean
        self._results['plot_pipelines_distance_dependence'] = self.plot_distance_dependence
        self._results['plot_pipelines_fc_fd_pearson'] = self.plot_fc_fd_pearson
        self._results['plot_pipelines_fc_fd_uncorr'] = self.perc_plot_fc_fd_uncorr
        self._results['plot_pipelines_tdof_loss'] = self.plot_tdof_loss

        return runtime

