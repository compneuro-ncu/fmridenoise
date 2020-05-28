from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
)

import numpy as np
import pandas as pd
from nilearn.connectome import sym_matrix_to_vec, vec_to_sym_matrix
from scipy.stats import pearsonr
from os.path import join
from itertools import chain
import warnings
from fmridenoise.utils.plotting import motion_plot


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

        self.pipeline_name = self.inputs.pipeline_name
        self.output_dir = self.inputs.output_dir
        self.quality_measures = []
        self.edges_weights = {}
        self.edges_weights_clean = {}
        self.sample_dict = {'All': True, 'No_high_motion': False}


    def _validate_group_conf_summary(self):
        """Checks if correct summary data are provided.
        Each row should contain data for one subject."""

        # Checks if file exist
        try:
            self.group_conf_summary = pd.read_csv(
                self.inputs.group_conf_summary, delimiter='\t')
        except FileNotFoundError:
            print('Missing confounds summary data file.')

        # Checks if file have data inside
        try:
            self.group_conf_summary.values
        except pd.errors.EmptyDataError:
            print('Missing confounds summary data')

        # Check if number of subjects corresponds to data frame size
        if len(self.group_conf_summary) != len(np.unique(self.group_conf_summary['subject'])):
            raise ValueError('Each subject should have only one ' +
                             'corresponding summary values.')

        # Check if summary contains data from a one task
        if len(np.unique(self.group_conf_summary['task'])) > 1:
            raise ValueError('Summary confouds data should contain ' +
                             'data from a one task at time.')

        # Check if subjects' data are not idenical
        if check_identity(self.group_conf_summary.iloc[:, 2:].values):
            raise ValueError('Confounds summary data of some subjects are identical.')

        # Check if number of subject allows to calculate summary measures
        if len(self.group_conf_summary['subject']) < 10:
            warnings.warn('Quality measures may be not meaningful ' +
                          'for small sample sizes.')

    def _validate_fc_matrices(self):
        """Checks if correct FC matrices are provided."""

        # Checks if file exists
        try:
            self.group_corr_mat = np.load(self.inputs.group_corr_mat)
        except FileNotFoundError:
            print('Missing group_corr_mat data file.')

        # Check if each matrix is symmetrical
        for matrix in self.group_corr_mat:
            if not check_symmetry(matrix):
                raise ValueError('Correlation matrix is not symetrical.')

        self.group_corr_vec = sym_matrix_to_vec(self.group_corr_mat)

        # Check if subjects' data are not idenical
        if check_identity(self.group_corr_vec):
            raise ValueError('Connectivity values of some subjects ' +
                             'are identical.')

        # Check if a number of FC matrices is the same as the nymber
        # of subjects
        if len(self.group_corr_vec) != len(self.group_conf_summary):
            raise ValueError('Number of FC matrices does not correspond ' +
                             'to the number of confound summaries.')

    def _validate_distance_matrix(self):
        """Validates distance matrix."""

        # Check if file exist
        try:
            self.distance_matrix = np.load(self.inputs.distance_matrix)
        except FileNotFoundError:
            print('Missing distance_matrix data file.')

        # Check if distance matrix has the same shape as FC matrix
        if self.group_corr_mat[0].shape != self.distance_matrix.shape:
            raise ValueError(f'FC matrices have shape {self.distance_matrix.shape} ' +
                             f'while distance matrix {self.group_corr_mat[0].shape}')

        self.distance_vector = sym_matrix_to_vec(self.distance_matrix)

    @property
    def n_subjects(self):
        """Returns total number of subjects."""
        return len(self.group_conf_summary)

    @property
    def subjects_list(self):
        """Returns list of all subjects."""
        return [f"sub-{sub + 1:02}" for sub in self.group_conf_summary['subject']]

    def _get_subject_filter(self, all_subjects=True):
        """Returns filter vector with subjects included in analysis."""
        if all_subjects:
            self.subject_filter = np.ones((self.n_subjects), dtype=bool)
        else:
            self.subject_filter = self.group_conf_summary['include'].values.astype('bool')

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
            fd = self.group_conf_summary['mean_fd'].values[subjects_filter]
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
        return self.group_conf_summary['n_conf'].mean()

    def _get_mean_edges_dict(self, subject_filter):
        """Greates fictionary with mean edge weights for selected subject filter."""
        self.edges_dict = {self.pipeline_name: self.group_corr_vec[subject_filter].mean(axis=0)}

    def _create_summary_dict(self, all_subjects=None, n_excluded=None):
        """Generates dictionary with all summary measures."""
        self.fc_fd_summary = {'pipeline': self.pipeline_name,
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
        for key, value in self.sample_dict.items():
            self._get_subject_filter(all_subjects=value)
            self._get_n_excluded(self.subject_filter)
            self._get_excluded_subjects(self.subject_filter)
            self._get_fc_fd_correlations(self.subject_filter)
            self._create_summary_dict(all_subjects=value, n_excluded=self.n_excluded)
            self.quality_measures.append(self.fc_fd_summary)
            self._get_mean_edges_dict(self.subject_filter)

            if value:
                self.edges_weight = self.edges_dict
            else:
                self.edges_weight_clean = self.edges_dict

    def _make_figures(self):
        """Generates figures."""
        motion_plot(self.group_conf_summary, self.pipeline_name, self.output_dir)

    def _run_interface(self, runtime):
        self._validate_group_conf_summary()
        self._validate_fc_matrices()
        self._validate_distance_matrix()
        self._quality_measures()
        self._make_figures()

        self._results['fc_fd_summary'] = self.quality_measures
        self._results['edges_weight'] = self.edges_weight
        self._results['edges_weight_clean'] = self.edges_weight_clean
        self._results['exclude_list'] = self.excluded_subjects

        return runtime


def check_identity(matrix):
    """Checks whether any row of the matrix is identical with any other row."""
    identical = []
    for a in range(len(matrix)):
        for b in range(a):
            identical.append(np.allclose(a, b, rtol=1e-05, atol=1e-08))
    return any(identical)


def check_symmetry(matrix):
    """Checks if matrix is symmetrical."""
    return np.allclose(matrix, matrix.T, rtol=1e-05, atol=1e-08)


class MergeGroupQualityMeasuresOutputSpec(TraitedSpec):
    fc_fd_summary = traits.List()
    edges_weight = traits.List()
    edges_weight_clean = traits.List()
    exclude_list = traits.Set(traits.Str())


class MergeGroupQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List()
    edges_weight = traits.List()
    edges_weight_clean = traits.List()
    exclude_list = traits.List(default=[])


class MergeGroupQualityMeasures(SimpleInterface):
    input_spec = MergeGroupQualityMeasuresInputSpec
    output_spec = MergeGroupQualityMeasuresOutputSpec
    

    def _run_interface(self, runtime):
        self._results['fc_fd_summary'] = self.inputs.fc_fd_summary
        self._results['edges_weight'] = self.inputs.edges_weight
        self._results['edges_weight_clean'] = self.inputs.edges_weight_clean
        self._results['exclude_list'] = set(chain(*chain(*self.inputs.exclude_list)))
        return runtime


class PipelinesQualityMeasuresInputSpec(BaseInterfaceInputSpec):

    fc_fd_summary = traits.List(
        exists=True,
        desc="QC-FC quality measures")

    edges_weight = traits.List(
        exists=True,
        desc="Weights of individual edges")

    edges_weight_clean = traits.List( # TODO: Fix me
        exists=True,
        desc="Weights of individual edges")

    output_dir = File(          # needed to save data in other directory
        desc="Output path")     # TODO: Implement temp dir

class PipelinesQualityMeasuresOutputSpec(TraitedSpec):

    pipelines_fc_fd_summary = File(
        exists=True,
        desc="Group QC-FC quality measures")

    pipelines_edges_weight = File(
        exists=True,
        desc="Group weights of individual edges")

    pipelines_edges_weight_clean = File(
        exists=True,
        desc="Group weights of individual edges")

    plot_pipeline_edges_density = File(
        exists=True,
        desc="Density of edge weights (all subjects)"
    )

    plot_pipelines_edges_density_no_high_motion = File(
        exist=True,
        desc="Density of edge weights (no high motion)"
    )

    plot_pipelines_fc_fd_pearson = File(
        exist=True
    )

    plot_pipelines_fc_fd_uncorr = File(
        exist=True
    )

    plot_pipelines_distance_dependence = File(
        exist=True
    )

    plot_pipelines_tdof_loss = File(
        exist=True
    )

class PipelinesQualityMeasures(SimpleInterface):
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec

    def _run_interface(self, runtime):

        # Convert merged quality measures to pd.DataFrame
        pipelines_fc_fd_summary = pd.DataFrame(
            list(chain.from_iterable(list(chain.from_iterable(self.inputs.fc_fd_summary)))))

        pipelines_edges_weight = pd.DataFrame()
        pipelines_edges_weight_clean = pd.DataFrame()

        for edges in zip(self.inputs.edges_weight):
            pipelines_edges_weight = pd.concat([pipelines_edges_weight, pd.DataFrame(edges[0][0])], axis=1)

        for edges_clean in zip(self.inputs.edges_weight_clean):
            pipelines_edges_weight_clean = pd.concat([pipelines_edges_weight_clean, pd.DataFrame(edges_clean[0][0])], axis=1)

        fname1 = join(self.inputs.output_dir, f"pipelines_fc_fd_summary.tsv")
        fname2 = join(self.inputs.output_dir, f"pipelines_edges_weight.tsv")
        fname3 = join(self.inputs.output_dir, f"pipelines_edges_weight_clean.tsv")

        pipelines_fc_fd_summary.to_csv(fname1, sep='\t', index=False)
        pipelines_edges_weight.to_csv(fname2, sep='\t', index=False)
        pipelines_edges_weight_clean.to_csv(fname3, sep='\t', index=False)

        # ----------------------
        # Plot quality measures
        # ----------------------

        # Reset color palette
        sns.set_palette("colorblind", 8)

        # Density plot (all subjects)
        fig1, ax = plt.subplots(1, 1)

        for col in pipelines_edges_weight:
            sns.kdeplot(pipelines_edges_weight[col], shade=True)
            plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
            plt.title("Density of edge weights (all subjects)")

        plot_pipeline_edges_density = f"{self.inputs.output_dir}/pipelines_edges_density.svg"
        fig1.savefig(plot_pipeline_edges_density, dpi=300,  bbox_inches='tight')
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        fig1.savefig(f"{self.inputs.output_dir}/pipelines_edges_density.svg", dpi=300,  bbox_inches='tight')

        # Density plot (no high motion)
        fig1_2, ax = plt.subplots(1, 1)

        for col in pipelines_edges_weight_clean:
            sns.kdeplot(pipelines_edges_weight_clean[col], shade=True)
            plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
            plt.title("Density of edge weights (no high motion)")
            plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        plot_pipelines_edges_density_no_high_motion = f"{self.inputs.output_dir}/pipelines_edges_density_no_high_motion.svg"
        fig1_2.savefig(plot_pipelines_edges_density_no_high_motion, dpi=300,  bbox_inches='tight')

        # Boxplot (Pearson's r FC-DC)
        fig2 = sns.catplot(x="pearson_fc_fd",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC (Pearson's r)",
                                    ylabel='Pipeline')

        plot_pipelines_fc_fd_pearson = f"{self.inputs.output_dir}/pipelines_fc_fd_pearson.svg"
        fig2.savefig(plot_pipelines_fc_fd_pearson, dpi=300, bbox_inches="tight")

        # Boxplot (% correlated edges)
        fig3 = sns.catplot(x="perc_fc_fd_uncorr",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC uncorrected (%)",
                                    ylabel='Pipeline')

        plot_pipelines_fc_fd_uncorr = f"{self.inputs.output_dir}/pipelines_fc_fd_uncorr.svg"
        fig3.savefig(plot_pipelines_fc_fd_uncorr, dpi=300, bbox_inches="tight")

        # Boxplot (Pearson's r FC-DC with distance)

        fig4 = sns.catplot(x="distance_dependence",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="Distance-dependence",
                                    ylabel='Pipeline')
        
        plot_pipelines_distance_dependence = f"{self.inputs.output_dir}/pipelines_distance_dependence.svg"
        fig4.savefig(plot_pipelines_distance_dependence, dpi=300, bbox_inches="tight")

        # Boxplot (fDOF-loss)

        fig5 = sns.catplot(x="tdof_loss",
                           y="pipeline",
                           kind='bar',
                           data=pipelines_fc_fd_summary,
                           orient="h").set(xlabel="fDOF-loss",
                                           ylabel='Pipeline')

        plot_pipelines_tdof_loss = f"{self.inputs.output_dir}/pipelines_tdof_loss.svg"
        fig5.savefig(plot_pipelines_tdof_loss, dpi=300, bbox_inches="tight")

        self._results['pipelines_fc_fd_summary'] = fname1
        self._results['pipelines_edges_weight'] = fname2
        self._results['pipelines_edges_weight_clean'] = fname3
        self._results['plot_pipeline_edges_density'] = plot_pipeline_edges_density
        self._results['plot_pipelines_distance_dependence'] = plot_pipelines_distance_dependence
        self._results['plot_pipelines_edges_density_no_high_motion'] = plot_pipelines_edges_density_no_high_motion
        self._results['plot_pipelines_fc_fd_pearson'] = plot_pipelines_fc_fd_pearson
        self._results['plot_pipelines_fc_fd_uncorr'] = plot_pipelines_fc_fd_uncorr
        self._results['plot_pipelines_tdof_loss'] = plot_pipelines_fc_fd_uncorr

        return runtime



