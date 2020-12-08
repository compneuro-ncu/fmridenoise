from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface, Str, File, traits)
import typing as t
import numpy as np
import pandas as pd
from nilearn.connectome import sym_matrix_to_vec, vec_to_sym_matrix
from scipy.stats import pearsonr, spearmanr
from os.path import join
import warnings

from traits.trait_base import Undefined, _Undefined
from traits.trait_types import List, Int, Instance, Dict, Union

from fmridenoise.utils.entities import build_path, parse_file_entities_with_pipelines, assert_all_entities_equal
from fmridenoise.utils.plotting import (make_motion_plot, make_kdeplot,
                                        make_catplot, make_violinplot, make_corr_matrix_plot)
from fmridenoise.utils.error_data import ErrorData
from fmridenoise.utils.traits import Optional


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

    pipeline = traits.Dict(mandatory=True,
                           desc="Pipeline")


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

    exclude_list = traits.Dict(
        exists=True,
        desc="Dictionary with all relevant entities information and list of subjects to exclude under excluded key")

    motion_plot = traits.File(
        exists=True,
        desc="Motion criterion plot"
    )

    corr_matrix_plot = traits.File(
        exists=True,
        desc="Fc-fd correlation matrix (no high motion)"
    )

    corr_matrix_no_high_motion_plot = traits.File(
        exists=False,
        desc="Fc-fd correlation matrix plot (no high motion)"
    )

    warnings = List(
        trait=Instance(ErrorData),
        value=[],
        desc="List with errors.")


class QualityMeasures(SimpleInterface):
    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec
    plot_pattern = "[ses-{session}_]task-{task}_[run-{run}_]pipeline-{pipeline}_desc-{desc}.svg"
    pval_tresh = 0.05

    def _validate_group_conf_summary(self, group_conf_summary: pd.DataFrame):
        """
        Checks if correct summary data are provided.
        Raises exceptions when data is not valid.
        Each row should contain data for one subject.
        """
        base_entities = parse_file_entities_with_pipelines(self.inputs.group_conf_summary)
        # Checks if file have data inside
        if group_conf_summary.empty:
            raise ValueError('Missing confounds summary data (empty dataframe)')
            # Checks if data frame contains proper columns
            # confounds_fields - from confound output definition
        all_possible_fields = {'subject', 'task', 'session', 'mean_fd', 'max_fd', 'n_conf', 'include', 'n_spikes',
                               'perc_spikes', 'run'}
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

        # Check if subjects' numerical data are not identical
        low_motion = len(group_conf_summary[group_conf_summary['include'] == True])
        if low_motion < 2:
            self._enough_clean_subjects = False
            self._warnings.append(ErrorData.error(
                entities=base_entities,
                source=self,
                message=f"Not enough low motion subjects found. Expected at least 2 but found {low_motion}"
            ))

        # Check if number of subject allows to calculate summary measures
        if len(group_conf_summary['subject']) < 10:
            self._warnings.append(ErrorData.warning(
                entities=base_entities,
                source=self,
                message='Quality measures may be not meaningful for small (lesser than 10) sample sizes.'
            ))

    @property
    def _warnings(self):
        if self._results.get('warnings') is None:
            self._results['warnings'] = []
        return self._results['warnings']

    @property
    def _enough_clean_subjects(self) -> bool:
        if not hasattr(self, "__enough_clean_subjects"):
            self._enough_clean_subjects = True
        return getattr(self, "__enough_clean_subjects")

    @_enough_clean_subjects.setter
    def _enough_clean_subjects(self, value: bool) -> None:
        setattr(self, "__enough_clean_subjects", value)

    @classmethod
    def _perc_fc_fd_uncorr(cls, fc_fd_pval: np.ndarray) -> float:
        """
        Calculates percent of significant FC-FD correlations (uncorrected).
        """
        return np.sum(fc_fd_pval < cls.pval_tresh) / len(fc_fd_pval) * 100

    @staticmethod
    def _distance_dependence(fc_fd_corr: np.ndarray, distance_vector: np.ndarray) -> float:
        """
        Calculates percent of significant FC-FD correlations (uncorrected).
        """
        return spearmanr(a=fc_fd_corr, b=distance_vector)[0]

    @staticmethod
    def calculate_fc_fd_correlations(group_conf_summary: pd.DataFrame,
                                     group_corr_vec: np.ndarray) -> t.Tuple[np.ndarray, np.ndarray]:
        """
        Calculates correlations between edges weights and mean framewise displacement.
        """
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
                         all_subjects: bool) -> t.Tuple[dict, np.ndarray, np.ndarray, t.List[str]]:
        """
        Calculates
        Args:
            group_conf_summary: Conf summary for all subjects
            distance_vec: Distance matrix flatten into vector
            group_corr_vec:
            all_subjects: True if all subjects should be included, False if only 'low motion' subjects

        Returns:
           Tuple with:
               dictionary with summary of various numerical parameters of processed data
               vector of mean correlations between edges
               vector of correlations between edges weights and mean framewise displacement
               list of excluded subjects
        """
        # select part of original dataset based on 'Include' parameter (all subjects or without high motion
        if all_subjects:
            group_conf_subsummary = group_conf_summary
            group_corr_subvec = group_corr_vec
        else:
            group_conf_subsummary = group_conf_summary[
                group_conf_summary['include'] == True]
            group_corr_subvec = group_corr_vec[group_conf_summary['include'].values.astype(bool), :]

        fc_fd_corr, fc_fd_pval = cls.calculate_fc_fd_correlations(group_conf_subsummary, group_corr_subvec)
        summary = {'perc_fc_fd_uncorr': cls._perc_fc_fd_uncorr(fc_fd_pval),
                   'median_pearson_fc_fd': np.median(np.abs(fc_fd_corr)),
                   'distance_dependence': cls._distance_dependence(fc_fd_corr, distance_vec),

                   'tdof_loss': group_conf_subsummary['n_conf'].mean(),
                   'n_subjects': len(group_conf_summary),
                   'n_excluded': len(group_conf_summary) - len(group_conf_subsummary),
                   'all': all_subjects,
                   }
        edges_weight = group_corr_subvec.mean(axis=0)
        excluded_subjects = group_conf_summary[group_conf_summary['include'] == False]['subject']
        return summary, edges_weight, fc_fd_corr, excluded_subjects

    def _calculate_quality_measures(
            self,
            group_conf_summary: pd.DataFrame,
            group_corr_mat: np.ndarray,
            distance_matrix: np.ndarray) -> \
            t.Tuple[t.List[dict], np.ndarray, np.ndarray, np.ndarray, np.ndarray, t.List[str]]:
        quality_measures = []
        excluded_subjects_names = set()
        group_corr_vec = sym_matrix_to_vec(group_corr_mat)
        distance_vec = sym_matrix_to_vec(distance_matrix)
        # all subjects
        summary, edges_weight, fc_fd_corr_vector, excluded_subjects = self._quality_measure(
            group_conf_summary,
            distance_vec,
            group_corr_vec, True)
        quality_measures.append(summary)
        excluded_subjects_names |= set(excluded_subjects)
        edges_weight_clean = Undefined
        fc_fd_corr_vector_clean = Undefined
        if self._enough_clean_subjects:
            # clean subjects (no high motion)
            summary, edges_weight_clean, fc_fd_corr_vector_clean, excluded_subjects = self._quality_measure(
                group_conf_summary, distance_vec, group_corr_vec, False)
            quality_measures.append(summary)
            excluded_subjects_names |= set(excluded_subjects)
        return quality_measures, edges_weight, edges_weight_clean, fc_fd_corr_vector, fc_fd_corr_vector_clean, \
               list(excluded_subjects_names)

    def _run_interface(self, runtime):
        # noinspection PyUnreachableCode
        if __debug__:
            entities = [parse_file_entities_with_pipelines(self.inputs.group_conf_summary),
                        parse_file_entities_with_pipelines(self.inputs.group_corr_mat)]
            assert_all_entities_equal(entities, "session", "run", "task", "pipeline")
        group_conf_summary_df = pd.read_csv(self.inputs.group_conf_summary, sep='\t', header=0)
        group_corr_mat_arr = np.load(self.inputs.group_corr_mat)
        distance_matrix_arr = np.load(self.inputs.distance_matrix)
        self._validate_group_conf_summary(group_conf_summary_df)

        summaries, edges_weight, edges_weight_clean, group_corr_vec, group_corr_vec_clean, exclude_list = \
            self._calculate_quality_measures(
                group_conf_summary_df,
                group_corr_mat_arr,
                distance_matrix_arr)
        pipeline_name = self.inputs.pipeline['name']
        for summary in summaries:
            summary['pipeline'] = pipeline_name
        # creating plots
        base_entities = parse_file_entities_with_pipelines(self.inputs.group_conf_summary)
        motion_plot_path = join(self.inputs.output_dir, build_path({**base_entities,
                                                                    'desc': 'motionCriterion_plot'},
                                                                   self.plot_pattern, strict=False))
        make_motion_plot(group_conf_summary_df, motion_plot_path)
        corr_matrix_plot = build_path({**base_entities,
                                       'desc': 'fcFdCorrMatrix_plot'},
                                      self.plot_pattern, strict=False)
        corr_matrix_plot = make_corr_matrix_plot(
            data=vec_to_sym_matrix(group_corr_vec),
            title=corr_matrix_plot.strip('.svg'),
            ylabel=base_entities['pipeline'],
            output_path=join(self.inputs.output_dir, corr_matrix_plot))
        corr_matrix_plot_no_high_motion = Undefined
        if self._enough_clean_subjects:
            corr_matrix_plot_no_high_motion = build_path(
                {**base_entities,
                 'desc': 'fcFdCorrMatrixNoHighMotion_plot'},
                self.plot_pattern, strict=False)
            corr_matrix_plot_no_high_motion = make_corr_matrix_plot(
                data=vec_to_sym_matrix(group_corr_vec_clean),
                title=corr_matrix_plot_no_high_motion.strip('.svg'),
                ylabel=base_entities['pipeline'],
                output_path=join(self.inputs.output_dir, corr_matrix_plot_no_high_motion))
        # setting output values
        self._results['fc_fd_summary'] = summaries
        self._results['edges_weight'] = {pipeline_name: edges_weight}
        if edges_weight_clean is not Undefined:
            self._results['edges_weight_clean'] = {pipeline_name: edges_weight_clean}
        self._results['fc_fd_corr_values'] = {pipeline_name: group_corr_vec}
        if group_corr_vec_clean is not Undefined:
            self._results['fc_fd_corr_values_clean'] = {pipeline_name: group_corr_vec_clean}
        self._results['exclude_list'] = {**base_entities, "excluded": exclude_list}
        self._results['motion_plot'] = motion_plot_path
        self._results['corr_matrix_plot'] = corr_matrix_plot
        self._results['corr_matrix_no_high_motion_plot'] = corr_matrix_plot_no_high_motion
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

    fc_fd_corr_values = traits.List(
        traits.Dict(
            exists=True,
            desc='Pearson r values for correlation '
                 'between FD and FC calculated for each edge'),
        desc="Pearson r values for correlation for each pipeline"
    )
    fc_fd_corr_values_clean = traits.List(
        Optional(
            Dict(
                exists=True,
                desc='Pearson r values for correlation '
                     'between FD and FC calculated for each edge'
                     'after removing subjects with high motion')),
        desc="Pearson r values for correlation for each pipeline (no high motion)"
    )
    edges_weight = traits.List(
        Dict(
            mandatory=True,
            desc="Weights of individual edges"),
        desc="Mean weights of individual edges for each pipeline"
    )

    edges_weight_clean = traits.List(
        Optional(
            Dict(
                desc="Mean weights of individual edges (no high motion)"),
        ),
        desc="Mean weights of individual edges for each pipeline (no high motion)"
    )

    task = Str(mandatory=True)
    session = Str(mandatory=False)
    run = Int(mandatory=False)

    output_dir = File(
        desc="Output path")


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
        exist=False,
        desc=""
    )

    plot_pipelines_fc_fd_pearson_no_high_motion = File(
        exist=False,
        desc=""
    )

    plot_pipelines_fc_fd_uncorr = File(
        exist=False,
        desc=""
    )

    plot_pipelines_distance_dependence = File(
        exist=False,
        desc=""
    )

    plot_pipelines_distance_dependence_no_high_motion = File(
        exists=False,
        desc=""
    )

    plot_pipelines_tdof_loss = File(
        exist=False,
        desc=""
    )


class PipelinesQualityMeasures(SimpleInterface):
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec
    plot_pattern = "[ses-{session}_]task-{task}_[run-{run}_]desc-{desc}_plot.svg"
    data_files_pattern = '[ses-{session}_]task-{task}[_run-{run}][_desc-{desc}]_{suffix}.{extension}'

    @staticmethod
    def pipeline_summaries_to_dataframe(pipelines_fd_fd_summary_raw: t.List[t.List[t.Dict]]) -> pd.DataFrame:
        """
        Converts standard fc_fd_summary from previous steps of data processing to
        dataframe
        Args:
            pipelines_fd_fd_summary_raw: list of 2 elements list (high motion and no high motion)
            with dictionaries containing information from quality measures interface output
            Check tests.manual.plotting_examples for reference data.
        Returns:
            dataframe with flatten input data
        """
        pipelines_fc_fd_summary = pd.DataFrame()

        for quality_measures in pipelines_fd_fd_summary_raw:
            for all_subjects_or_no in quality_measures:
                pipelines_fc_fd_summary = pd.concat([pipelines_fc_fd_summary,
                                                     pd.DataFrame(all_subjects_or_no, index=[0])],
                                                    axis=0)
        return pipelines_fc_fd_summary

    @staticmethod
    def edges_weight_to_dataframe(
            edges_weight: t.List[t.Dict[str, np.ndarray]],
            edges_weight_clean: t.List[t.Union[_Undefined, t.Dict[str, np.ndarray]]]) -> t.Tuple[
        pd.DataFrame, pd.DataFrame]:
        """
        Converts input (input spec) edges_weight and edges_weight_clean from previous steps of data processing
        to dataframe
        Args:
            edges_weight: list of dictionaries with pipeline name and array of floats
            edges_weight_clean: list of dictionaries with pipeline name and array of floats

        Returns:
            dataframe with flatten input data
        """
        pipelines_edges_weight = pd.DataFrame()
        pipelines_edges_weight_clean = pd.DataFrame()

        for edges, edges_clean in zip(edges_weight, edges_weight_clean):
            pipeline_name = list(edges.keys())[0]
            pipelines_edges_weight = pd.concat([pipelines_edges_weight,
                                                pd.DataFrame(edges,
                                                             columns=[pipeline_name])],
                                               axis=1)
            if edges_clean is not Undefined:
                pipelines_edges_weight_clean = pd.concat([pipelines_edges_weight_clean,
                                                          pd.DataFrame(edges_clean,
                                                                       columns=[pipeline_name])],
                                                         axis=1)
        return pipelines_edges_weight, pipelines_edges_weight_clean

    @staticmethod
    def fc_fd_corr_values_to_dataframe(
            fc_fd_corr_values: t.List[t.Dict[str, np.ndarray]],
            fc_fd_corr_values_clean: t.List[t.Union[_Undefined, t.Dict[str, np.ndarray]]]) -> t.Tuple[
        pd.DataFrame, pd.DataFrame]:
        """
        Converts input (input spec) fc_fd_corr_values and fc_fd_corr_values_clean from previous steps of data processing
        to dataframe
        Args:
            fc_fd_corr_values: list of dictionaries with pipeline name and array of floats
            fc_fd_corr_values_clean: list of dictionaries with pipeline name and array of floats

        Returns:
            dataframe with flatten input data
        """
        pipelines_fc_fd_values = pd.DataFrame()
        pipelines_fc_fd_values_clean = pd.DataFrame()

        for corr, corr_clean in zip(fc_fd_corr_values, fc_fd_corr_values_clean):
            pipeline_name = list(corr.keys())[0]
            pipelines_fc_fd_values = pd.concat([pipelines_fc_fd_values,
                                                pd.DataFrame(corr,
                                                             columns=[pipeline_name])],
                                               axis=1)
            if corr_clean is not Undefined:
                pipelines_fc_fd_values_clean = pd.concat([pipelines_fc_fd_values_clean,
                                                          pd.DataFrame(corr_clean,
                                                                       columns=[pipeline_name])],
                                                         axis=1)
        return pipelines_fc_fd_values, pipelines_fc_fd_values_clean

    def _make_summary_figures(self, entities_dict: dict) -> None:
        """
        Makes summary figures for all quality measures
        """
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'pipelinesEdgesDensity'},
                                                       self.plot_pattern, strict=False))
        self.plot_pipelines_edges_density = make_kdeplot(data=self.pipelines_edges_weight,
                                                         title="Density of edge weights (all subjects)",
                                                         output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'pipelinesEdgesDensityNoHighMotion'},
                                                       self.plot_pattern, strict=False))
        self.plot_pipelines_edges_density_clean = make_kdeplot(data=self.pipelines_edges_weight_clean,
                                                               title="Density of edge weights (no high motion)",
                                                               output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'fcFdPearson'},
                                                       self.plot_pattern, strict=False))
        self.plot_fc_fd_pearson = make_catplot(x="median_pearson_fc_fd",
                                               y='pipeline',
                                               data=self.pipelines_fc_fd_summary[
                                                   self.pipelines_fc_fd_summary['all'] == True],
                                               xlabel="Median QC-FC (Pearson's r)",
                                               output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'fcFdPearsonNoHighMotion'},
                                                       self.plot_pattern, strict=False))
        self.plot_fc_fd_pearson_no_high_motion = make_catplot(
            x="median_pearson_fc_fd",
            y='pipeline',
            data=self.pipelines_fc_fd_summary[self.pipelines_fc_fd_summary['all'] == False],
            xlabel="Median QC-FC (Pearson's r) (no high motion)",
            output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'percFcFdUncorr'},
                                                       self.plot_pattern, strict=False))
        self.perc_plot_fc_fd_uncorr = make_catplot(x="perc_fc_fd_uncorr",
                                                   y='pipeline',
                                                   data=self.pipelines_fc_fd_summary,
                                                   xlabel="QC-FC uncorrected (%)",
                                                   output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'distanceDependence'},
                                                       self.plot_pattern, strict=False))
        self.plot_distance_dependence = make_catplot(x="distance_dependence",
                                                     y='pipeline',
                                                     data=self.pipelines_fc_fd_summary[
                                                         self.pipelines_fc_fd_summary['all'] == True],
                                                     xlabel="Distance-dependence",
                                                     output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'distanceDependenceNoHighMotion'},
                                                       self.plot_pattern, strict=False))
        self.plot_distance_dependence_no_high_motion = make_catplot(
            x="distance_dependence",
            y='pipeline',
            data=self.pipelines_fc_fd_summary[self.pipelines_fc_fd_summary['all'] == False],
            xlabel="Distance-dependence (no high motion)",
            output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'tdofLoss'},
                                                       self.plot_pattern, strict=False))
        self.plot_tdof_loss = make_catplot(x="tdof_loss",
                                           y='pipeline',
                                           data=self.pipelines_fc_fd_summary,
                                           xlabel="fDOF-loss",
                                           output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'violinPlot'},
                                                       self.plot_pattern, strict=False))
        self.plot_violin_plot = make_violinplot(data=self.pipelines_fc_fd_values,
                                                xlabel="fc_fd_correlation",
                                                output_path=path)
        path = join(self.inputs.output_dir, build_path({**entities_dict, 'desc': 'violinPlotNoHighMotion'},
                                                       self.plot_pattern, strict=False))
        self.plot_violin_plot = make_violinplot(data=self.pipelines_fc_fd_values_clean,
                                                xlabel="fc_fd_correlation",
                                                output_path=path)

    def _run_interface(self, runtime):
        self.pipelines_fc_fd_summary = self.pipeline_summaries_to_dataframe(self.inputs.fc_fd_summary)
        self.pipelines_edges_weight, self.pipelines_edges_weight_clean = self.edges_weight_to_dataframe(
            self.inputs.edges_weight, self.inputs.edges_weight_clean)
        self.pipelines_fc_fd_values, self.pipelines_fc_fd_values_clean = self.fc_fd_corr_values_to_dataframe(
            self.inputs.fc_fd_corr_values, self.inputs.fc_fd_corr_values_clean)
        self.entities_dict = {'task': self.inputs.task}
        if self.inputs.run:
            self.entities_dict['run'] = self.inputs.run
        if self.inputs.session:
            self.entities_dict['session'] = self.inputs.session
        figures_entites = self.entities_dict.copy()

        self._make_summary_figures(figures_entites)
        self.entities_dict['suffix'] = 'pipelinesFcFdSummary'
        self.entities_dict['extension'] = '.tsv'
        pipelines_fc_fd_summary_file = join(self.inputs.output_dir,
                                            build_path(self.entities_dict, self.data_files_pattern, strict=False))
        self.pipelines_fc_fd_summary.to_csv(pipelines_fc_fd_summary_file, sep='\t', index=False)
        self.entities_dict['suffix'] = 'pipelinesEdgesWeight'
        self.entities_dict['extension'] = 'tsv'
        pipelines_edges_weigh_file = join(self.inputs.output_dir,
                                          build_path(self.entities_dict, self.data_files_pattern, strict=False))
        self.pipelines_edges_weight.to_csv(pipelines_edges_weigh_file, sep='\t', index=False)
        self.entities_dict['suffix'] = 'pipelinesEdgesWeightClean'
        self.entities_dict['extension'] = 'tsv'
        pipelines_edges_weight_clean_file = join(self.inputs.output_dir,
                                                 build_path(self.entities_dict, self.data_files_pattern, strict=False))
        self.pipelines_edges_weight_clean.to_csv(pipelines_edges_weight_clean_file, sep='\t', index=False)

        self._results['pipelines_fc_fd_summary'] = pipelines_fc_fd_summary_file
        self._results['pipelines_edges_weight'] = pipelines_edges_weigh_file
        self._results['pipelines_edges_weight_clean'] = pipelines_edges_weight_clean_file
        self._results['plot_pipelines_edges_density'] = self.plot_pipelines_edges_density
        self._results['plot_pipelines_edges_density_no_high_motion'] = self.plot_pipelines_edges_density_clean
        self._results['plot_pipelines_distance_dependence'] = self.plot_distance_dependence
        self._results[
            'plot_pipelines_distance_dependence_no_high_motion'] = self.plot_distance_dependence_no_high_motion
        self._results['plot_pipelines_fc_fd_pearson'] = self.plot_fc_fd_pearson
        self._results['plot_pipelines_fc_fd_pearson_no_high_motion'] = self.plot_fc_fd_pearson_no_high_motion
        self._results['plot_pipelines_fc_fd_uncorr'] = self.perc_plot_fc_fd_uncorr
        self._results['plot_pipelines_tdof_loss'] = self.plot_tdof_loss

        return runtime
