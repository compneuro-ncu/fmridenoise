from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    File,
    traits
)
import typing as t
import numpy as np
import pandas as pd
from nilearn.connectome import sym_matrix_to_vec
from scipy.stats import pearsonr
from os.path import join
import warnings
from fmridenoise.utils.plotting import make_motion_plot, make_kdeplot, make_catplot
from fmridenoise.utils.numeric import array_2d_row_identity, check_symmetry
from fmridenoise.utils.entities import EntityDict


class QualityMeasuresInputSpec(BaseInterfaceInputSpec):
    group_corr_mat = File(exists=True,
                          desc='Group connectivity matrix',
                          mandatory=True)

    group_conf_summary = File(exists=True,
                              desc='Group confounds summary',
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

    def __init__(self,
                 *args, **kwargs):
        """
        Initializes QualityMeasures interface.
        group_conf_summary, group_corr_mat and distance_matrix are optional parameters meant to be provided
        if interfaces is used as standalone class and not part of nipype workflow
        _run_interface overwrites values provided in __init__
        Args:
            group_conf_summary:
            group_corr_mat_arr:
            distance_matrix_arr:
            *args: nipype optional arguments
            **kwargs: nipype optional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.edges_weights = {}
        self.edges_weights_clean = {}
        self.sample_dict = {'All': True, 'No_high_motion': False}
        self.__group_corr_vec_cache = None  # cache for self.group_corr_vec
        self.__distance_vector_cache = None  # cache for self.distance_vector
        self.group_conf_summary_df: pd.DataFrame = ...  # initialized in _run_interface
        self.group_corr_mat_arr: np.ndarray = ...  # initialized in _run_interface
        self.distance_matrix_arr: np.ndarray = ...  # initialized in _run_interface

    def _validate_group_conf_summary(self) -> None:  # TODO: Create test cases for validation covering all scenarios
        """Checks if correct summary data are provided.
        Each row should contain data for one subject."""

        # Checks if file have data inside
        if self.group_conf_summary_df.empty:
            raise ValueError('Missing confounds summary data (empty dataframe)')
        # Checks if data frame contains proper columns
        # confounds_fields - from confound output definition
        all_possible_fields = {'subject', 'task', 'session', 'mean_fd', 'max_fd', 'n_conf', 'include', 'n_spikes', 'perc_spikes'}
        mandatory_fields = {'subject', 'task', 'mean_fd', 'max_fd', 'n_conf', 'include'}
        provided_fields = set(self.group_conf_summary_df.columns)
        excess_fields = provided_fields - all_possible_fields
        mandatory_provided = provided_fields >= mandatory_fields
        if not mandatory_provided:
            raise ValueError(f'Confounds file require to have columns of\n{mandatory_fields}\n'
                             f'but data frame contains only columns of\n{self.group_conf_summary_df.columns}')
        if len(excess_fields) > 0:
            raise ValueError(f"Confounds file has excess fields {excess_fields}, check input dataframe")

        # Check if number of subjects corresponds to data frame size
        if len(self.group_conf_summary_df) != len(np.unique(self.group_conf_summary_df['subject'])):
            raise ValueError('Each subject should have only one ' +
                             'corresponding summary values.')

        # Check if summary contains data from a one task
        if len(np.unique(self.group_conf_summary_df['task'])) > 1:
            raise ValueError('Summary confouds data should contain ' +
                             'data from a one task at time.')

        # Check if subjects' numerical data are not identical
        num_data_columns = {'mean_fd', 'max_fd', 'n_conf', 'n_spikes', 'perc_spikes'}
        result = array_2d_row_identity(self.group_conf_summary_df[provided_fields & num_data_columns].values)
        if result is not False:
            raise ValueError('Confounds summary data of some subjects are identical')

        # Check if number of subject allows to calculate summary measures
        if len(self.group_conf_summary_df['subject']) < 10:
            warnings.warn('Quality measures may be not meaningful ' +
                          'for small (lesser than 10) sample sizes.')  # TODO: Maybe push all messages like this to interface output and present it in final raport?

    def _validate_fc_matrices(self) -> None:  # NOTE: A bit of anti-patter. Name of method - validate something.
                                      #       Does not corespond to it's functionality which validades value
                                      #       AND assigns new object variable.
        """Checks if correct FC matrices are provided."""

        # Check if each matrix is symmetrical
        for matrix in self.group_corr_mat_arr:
            if not check_symmetry(matrix):
                raise ValueError('Correlation matrix is not symmetrical.')

        # Check if subjects' data are not identical
        if array_2d_row_identity(self.group_corr_vec) is not False:
            raise ValueError('Connectivity values of some subjects ' +
                             'are identical.')

        # Check if a number of FC matrices is the same as the number
        # of subjects
        if len(self.group_corr_vec) != len(self.group_conf_summary_df):
            raise ValueError('Number of FC matrices does not correspond ' +
                             'to the number of confound summaries.')

    def _validate_distance_matrix(self) -> None:
        """Validates distance matrix."""

        # Check if distance matrix has the same shape as FC matrix
        if self.group_corr_mat_arr[0].shape != self.distance_matrix_arr.shape:
            raise ValueError(f'FC matrices have shape {self.group_corr_mat_arr.shape} ' +
                             f'while distance matrix {self.distance_matrix_arr.shape}')

    @property
    def n_subjects(self) -> int:
        """Returns total number of subjects."""
        return len(self.group_conf_summary_df)

    @property
    def subjects_list(self) -> t.List[str]:
        """Returns list of all subjects."""
        return [f"sub-{sub}" for sub in self.group_conf_summary_df['subject']]

    @property  # TODO: Implement cached_property/changed to functools.cached_property after update to Python 3.8
    def group_corr_vec(self) -> np.ndarray:
        if self.__group_corr_vec_cache is None:
            self.__group_corr_vec_cache = sym_matrix_to_vec(self.group_corr_mat_arr)
        return self.__group_corr_vec_cache

    @property  # TODO: Implement cached_property/changed to functools.cached_property after update to Python 3.8
    def distance_vector(self) -> np.ndarray:
        if self.__distance_vector_cache is None:
            self.__distance_vector_cache = sym_matrix_to_vec(self.distance_matrix_arr)
        return self.__distance_vector_cache

    def _get_subject_filter(self, all_subjects=True) -> np.ndarray:
        """Returns filter vector with subjects included in analysis."""
        if all_subjects:
            return np.ones(self.n_subjects, dtype=bool)
        else:
            return self.group_conf_summary_df['include'].values.astype('bool')

    def _get_excluded_subjects(self, subjects_filter: t.Iterable[bool]) -> t.List[str]:
        """
        Returns list of subjects where value in subject_filter is False
        Args:
            subject_list: subject codes
            subjects_filter: boolean values where False mean subject to exclude

        Returns: list containing excluded subjects codes
        """
        ret = [ self.group_conf_summary_df['subject'][index] for index, boolean in enumerate(subjects_filter) if not boolean ]
        return ret

    def _get_fc_fd_correlations(self, subjects_filter) -> t.Tuple[np.ndarray, np.ndarray]:
        """Calculates correlations between edges weights and mean framewise displacement
        for all subjects."""
        n_edges = self.group_corr_vec.shape[1]
        fc_fd_corr, fc_fd_pval = (np.zeros(n_edges) for _ in range(2))
        fd = self.group_conf_summary_df['mean_fd'].values[subjects_filter]
        for i in range(n_edges):
            fc = self.group_corr_vec[subjects_filter, i]
            corr = pearsonr(x=fc, y=fd)
            fc_fd_corr[i], fc_fd_pval[i] = corr

        if np.isnan(fc_fd_corr).any():
            fc_fd_corr = np.nan_to_num(fc_fd_corr)
            warnings.warn('NaN values in correlation measues; ' +
                          'replaced with zeros.')
        return fc_fd_corr, fc_fd_pval

    def pearson_fc_fd_median(self):
        """Calculates median of FC-FD correlations."""
        return np.median(self.fc_fd_corr)

    def perc_fc_fd_uncorr(self):
        """Calculates percent of significant FC-FD correlations (uncorrected)."""
        return np.sum(self.fc_fd_pval < 0.05) / len(self.fc_fd_pval) * 100

    def distance_dependence(self):
        """Calculates distance dependence of FC-FD correlations."""
        return pearsonr(self.fc_fd_corr, self.distance_vector)[0]

    def dof_loss(self): # TODO: Shouldn't there be subject filter???
        """Calculates degrees of freedom loss."""
        return self.group_conf_summary_df['n_conf'].mean()

    def _get_mean_edges_dict(self, subject_filter):
        """Greates fictionary with mean edge weights for selected subject filter."""
        return {self.inputs.pipeline_name: self.group_corr_vec[subject_filter].mean(axis=0)}

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
        for key, value in self.sample_dict.items():  # TODO: Result of the function depends on True/False order in self.sample_dict
            subject_filter = self._get_subject_filter(all_subjects=value)
            self.excluded_subjects = self._get_excluded_subjects(subject_filter) # TODO: Get rid of excluded subjects
            n_excluded = len(self.excluded_subjects)
            self.fc_fd_corr, self.fc_fd_pval = self._get_fc_fd_correlations(subject_filter)
            summary = self._create_summary_dict(all_subjects=value, n_excluded=n_excluded)
            quality_measures.append(summary)
            edges_dict = self._get_mean_edges_dict(subject_filter)

            if value:
                self.edges_weight = edges_dict
            else:
                self.edges_weight_clean = edges_dict
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


class PipelinesQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List(
        traits.List(
            traits.Dict(
                desc="QC-FC quality measures"),
            desc="QC-FC quality measure for all subjects and without excluded subjects"
        ),
        desc="QC-FC quality measures for each pipeline"
    )

    edges_weight = traits.List(
        traits.Dict(
            mandatory=True,
            desc="Weights of individual edges"),
        desc="Mean weights of individual edges for each pipeline"
    )

    edges_weight_clean = traits.List(
        traits.Dict(
             desc="Mean weights of individual edges (no high motion)"),
        desc="Mean weights of individual edges for each pipeline (no high motion)"
    )

    output_dir = File(  # needed to save data in other directory
        desc="Output path")  # TODO: Implement temp dir

    task = traits.Str(
        desc="Task name")

    session = traits.Str(
        desc="Session name")


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

    plot_pipelines_edges_density = File(
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

    plot_pipelines_tdof_loss = File(  # TODO: Include in final report?
        exist=False
    )


class PipelinesQualityMeasures(SimpleInterface):
    # TODO: Check density edges plot - looks suspicious
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec

    def _get_pipeline_summaries(self) -> pd.DataFrame:
        """Gets and saves table with quality measures for each pipeline"""
        self.pipelines_fc_fd_summary = pd.DataFrame()

        for quality_measures in self.inputs.fc_fd_summary:
            for all_subjects_or_no in quality_measures:
                self.pipelines_fc_fd_summary = pd.concat([self.pipelines_fc_fd_summary,
                                                          pd.DataFrame(all_subjects_or_no, index=[0])],
                                                          axis=0)
        return self.pipelines_fc_fd_summary

    def _get_pipelines_edges_weight(self):
        """Gets and saves tables with mean edges weights for raw and cleaned data"""
        self.pipelines_edges_weight = pd.DataFrame()
        self.pipelines_edges_weight_clean = pd.DataFrame()

        for edges, edges_clean in zip(self.inputs.edges_weight, self.inputs.edges_weight_clean):
            pipeline_name = list(edges.keys())[0]
            self.pipelines_edges_weight = pd.concat([self.pipelines_edges_weight,
                                                     pd.DataFrame(edges,
                                                                  columns=[pipeline_name])],
                                                    axis=1)
            self.pipelines_edges_weight_clean = pd.concat([self.pipelines_edges_weight_clean,
                                                           pd.DataFrame(edges_clean,
                                                                        columns=[pipeline_name])],
                                                          axis=1)
        return self.pipelines_edges_weight, self.pipelines_edges_weight_clean

    def _make_summary_figures(self, entities_dict):
        """Makes summary figures for all quality mesures"""
        if 'extension' in entities_dict.keys():
            del entities_dict['extension']
        entities_dict.overwrite('suffix', 'pipelinesEdgesDensity')
        self.plot_pipelines_edges_density = make_kdeplot(data=self.pipelines_edges_weight,
                                                         title="Density of edge weights (all subjects)",
                                                         filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                                         output_dir=self.inputs.output_dir)
        entities_dict.overwrite('suffix', 'pipelinesEdgesDensityNoHighMotion')
        self.plot_pipelines_edges_density_clean = make_kdeplot(data=self.pipelines_edges_weight_clean,
                                                               title="Density of edge weights (no high motion)",
                                                               filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                                               output_dir=self.inputs.output_dir)
        entities_dict.overwrite('suffix', 'fcFdPearson')
        self.plot_fc_fd_pearson = make_catplot(x="pearson_fc_fd",
                                               data=self.pipelines_fc_fd_summary,
                                               xlabel="QC-FC (Pearson's r)",
                                               filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                               output_dir=self.inputs.output_dir)
        entities_dict.overwrite('suffix', 'percFcFdUncorr')
        self.perc_plot_fc_fd_uncorr = make_catplot(x="perc_fc_fd_uncorr",
                                                   data=self.pipelines_fc_fd_summary,
                                                   xlabel="QC-FC uncorrected (%)",
                                                   filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                                   output_dir=self.inputs.output_dir)
        entities_dict.overwrite('suffix', 'distanceDependence')
        self.plot_distance_dependence = make_catplot(x="distance_dependence",
                                                     data=self.pipelines_fc_fd_summary,
                                                     xlabel="Distance-dependence",
                                                     filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                                     output_dir=self.inputs.output_dir)
        entities_dict.overwrite('suffix', 'tdofLoss')
        self.plot_tdof_loss = make_catplot(x="tdof_loss",
                                           data=self.pipelines_fc_fd_summary,
                                           xlabel="fDOF-loss",
                                           filename=entities_dict.build_filename({'ses': False, 'task': True}),
                                           output_dir=self.inputs.output_dir)

    def _run_interface(self, runtime):
        summary = self._get_pipeline_summaries()
        pipelines_edges_weight, pipelines_edges_weight_clean = self._get_pipelines_edges_weight()
        self.entities_dict = EntityDict(task=self.inputs.task)
        if self.inputs.session != traits.Undefined:
            self.entities_dict['session'] = self.inputs.session
        self._make_summary_figures(self.entities_dict)
        self.entities_dict.overwrite('suffix', 'pipelinesFcFdSummary')
        self.entities_dict.overwrite('extension', 'tsv')
        pipelines_fc_fd_summary_file = join(self.inputs.output_dir, self.entities_dict.build_filename({
            'ses': False,
            'task': True}))
        summary.to_csv(pipelines_fc_fd_summary_file, sep='\t', index=False)
        self.entities_dict.overwrite('suffix', 'pipelinesEdgesWeight')
        self.entities_dict.overwrite('extension', 'tsv')
        pipelines_edges_weigh_file = join(self.inputs.output_dir, self.entities_dict.build_filename({'ses': False, 'task': True}))
        pipelines_edges_weight.to_csv(pipelines_edges_weigh_file, sep='\t', index=False)
        self.entities_dict.overwrite('suffix', 'pipelinesEdgesWeightClean')
        self.entities_dict.overwrite('extension', 'tsv')
        pipelines_edges_weight_clean_file = join(self.inputs.output_dir, self.entities_dict.build_filename({'ses': False, 'task': True}))
        pipelines_edges_weight_clean.to_csv(pipelines_edges_weight_clean_file, sep='\t', index=False)

        self._results['pipelines_fc_fd_summary'] = pipelines_fc_fd_summary_file
        self._results['pipelines_edges_weight'] = pipelines_edges_weigh_file
        self._results['pipelines_edges_weight_clean'] = pipelines_edges_weight_clean_file
        self._results['plot_pipelines_edges_density'] = self.plot_pipelines_edges_density
        self._results['plot_pipelines_edges_density_no_high_motion'] = self.plot_pipelines_edges_density_clean
        self._results['plot_pipelines_distance_dependence'] = self.plot_distance_dependence
        self._results['plot_pipelines_fc_fd_pearson'] = self.plot_fc_fd_pearson
        self._results['plot_pipelines_fc_fd_uncorr'] = self.perc_plot_fc_fd_uncorr
        self._results['plot_pipelines_tdof_loss'] = self.plot_tdof_loss

        return runtime

