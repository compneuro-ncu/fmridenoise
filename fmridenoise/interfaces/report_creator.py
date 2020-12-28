import os
from pathlib import Path
from shutil import copyfile
from frozendict import frozendict
from itertools import chain

from traits.trait_types import Dict, Directory, File, List, Str, Int, Instance

from fmridenoise.utils.dataclasses.excluded_subjects import ExcludedSubjects
from fmridenoise.utils.entities import parse_file_entities_with_pipelines, build_path, is_entity_subset
from fmridenoise.utils.error_data import ErrorData
from fmridenoise.utils.report_creator import create_report
from nipype.interfaces.base import BaseInterfaceInputSpec, SimpleInterface
from fmridenoise.utils.dataclasses.runtime_info import RuntimeInfo
from fmridenoise.utils.traits import Optional, remove_undefined


class ReportCreatorInputSpec(BaseInterfaceInputSpec):
    pipelines = List(
        Dict("Dictionary pipeline"),
        mandatory=True
    )
    tasks = List(
        Str(), mandatory=True)
    output_dir = Directory(exists=True)
    sessions = List(
        Str(),
        mandatory=False)
    runs = List(
        Int(), mandatory=False)
    runtime_info = Instance(RuntimeInfo, mandatory=True)
    excluded_subjects = List(
        trait=Instance(ExcludedSubjects),
        value=[],
        usedefault=True
    )

    warnings = List(
        trait=Instance(ErrorData),
        desc="ErrorData objects with all relevant entities error source and error message",
        value=[],
        usedefault=True
    )

    # Aggregated over pipelines
    plots_all_pipelines_edges_density = List(
        Optional(
            File(
                exists=True,
                desc="Density of edge weights (all pipelines) for all subjects"
            )))

    plots_all_pipelines_edges_density_no_high_motion = List(
        Optional(
            File(
                exists=True,
                desc="Density of edge weights (all pipelines) without high motion subjects"
            )))

    plots_all_pipelines_fc_fd_pearson_info = List(
        Optional(File(
            exists=True,
            desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values for all subjects"
        )))

    plots_all_pipelines_fc_fd_pearson_info_no_high_motion = List(
        Optional(
            File(
                exists=True,
                desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values without high motion subjects"
            )))

    plots_all_pipelines_distance_dependence = List(
        Optional(
            File(
                exists=True,
                desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs for all subject"
            )))

    plots_all_pipelines_distance_dependence_no_high_motion = List(
        Optional(
            File(
                exists=True,
                desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs without high motion subjects"
            )))

    plots_all_pipelines_tdof_loss = List(
        Optional(
            File(
                exists=True,
                desc="Barplot showing degree of freedom loss (number of regressors included in each pipeline."
            )))

    # For single pipeline
    plots_pipeline_fc_fd_pearson_matrix = List(
        Optional(
            File(
                exists=True,
                desc="Matrix showing correlation between connection strength and motion for all subjects"
            )))

    plots_pipeline_fc_fd_pearson_matrix_no_high_motion = List(
        Optional(
            File(
                exists=True,
                desc="Matrix showing correlation between connection strength and motion without high motion subjects"
            )))


class ReportCreator(SimpleInterface):
    input_spec = ReportCreatorInputSpec

    _always_run = True

    def _run_interface(self, runtime):
        # Find all distinct entities
        plots_all_pipelines, plots_pipeline = {}, {}
        for plots_type, plots_list in self.inputs.__dict__.items():

            if (plots_type.startswith('plots_all_pipelines')
                    and isinstance(plots_list, list)):
                plots_all_pipelines[plots_type] = list(remove_undefined(plots_list))

            if (plots_type.startswith('plots_pipeline')
                    and isinstance(plots_list, list)):
                plots_pipeline[plots_type] = list(remove_undefined(plots_list))

        unique_entities = set(
            map(lambda path: frozendict(filter(
                lambda pair: pair[0] in ['session', 'task', 'run'],
                parse_file_entities_with_pipelines(path).items())),
                chain(*chain(plots_all_pipelines.values(), plots_pipeline.values()))))

        unique_pipelines = set(pipeline['name'] for pipeline in self.inputs.pipelines)
        # Create input for create_report
        figures_dir = Path(self.inputs.output_dir).joinpath('figures')
        figures_dir.mkdir(parents=True, exist_ok=True)
        report_data = []

        for entity in unique_entities:

            entity_data = {'entity_name': build_path(entity, "[ses-{session}] task-{task} [run-{run}]"),
                           'entity_id': build_path(entity, "[ses-{session}-]task-{task}[-run-{run}]"),
                           'excluded_subjects': set(),
                           'warnings': [],
                           'errors': [],
                           'pipeline': []}
            # Manage excluded subjects
            for excluded in self.inputs.excluded_subjects:
                if is_entity_subset(excluded.entities, entity):
                    entity_data['excluded_subjects'] |= excluded.excluded
            entity_data['excluded_subjects'] = str(entity_data['excluded_subjects']).lstrip('{').rstrip(
                        '}') if len(entity_data['excluded_subjects']) > 1 else []
            # Manage errors and warnings
            for error in self.inputs.warnings:
                if is_entity_subset(error.entities, entity):
                    if error.critical:
                        entity_data['errors'].append(error.build_message())
                    else:
                        entity_data['warnings'].append(error.build_message())

            # Manage plots for all_pipelines
            for plots_type, plots_list in plots_all_pipelines.items():
                for plot in plots_list:
                    if is_entity_subset(parse_file_entities_with_pipelines(plot), entity):
                        plot_basename = os.path.basename(plot)
                        plot_relative_path = os.path.join('figures', plot_basename)
                        copyfile(plot, os.path.join(figures_dir, plot_basename))
                        entity_data[plots_type] = plot_relative_path
                        break

            # Manage plots for single pipeline
            for pipeline in unique_pipelines:
                pipeline_data = {
                    'pipeline_dict': next(pipeline_dict
                                          for pipeline_dict
                                          in self.inputs.pipelines
                                          if pipeline_dict['name'] == pipeline)
                }

                # Manage plots for single pipeline
                for plots_type, plots_list in plots_pipeline.items():
                    for plot in plots_list:
                        if pipeline in plot and is_entity_subset(parse_file_entities_with_pipelines(plot), entity):
                            plot_basename = os.path.basename(plot)
                            plot_relative_path = os.path.join('figures', plot_basename)
                            copyfile(plot, os.path.join(figures_dir, plot_basename))
                            pipeline_data[plots_type] = plot_relative_path

                # append new pipeline data dict
                entity_data['pipeline'].append(pipeline_data)

            # append new entity data dict
            report_data.append(entity_data)
        # sort report data
        report_data.sort(key=lambda x: dict.get(x, "entity_name"))
        # Create report
        create_report(
            runtime_info=self.inputs.runtime_info,
            report_data=report_data,
            output_dir=self.inputs.output_dir,
            report_name='fMRIdenoise_report.html'
        )

        return runtime
