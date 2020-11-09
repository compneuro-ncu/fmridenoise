import os
from pathlib import Path
from shutil import copyfile
from fmridenoise.utils.entities import parse_file_entities, build_path, is_entity_subset
from fmridenoise.utils.report_creator import create_report
from nipype.interfaces.base import BaseInterfaceInputSpec, SimpleInterface
from traits.trait_types import Dict, Directory, File, List, Str
from frozendict import frozendict
from itertools import chain


class ReportCreatorInputSpec(BaseInterfaceInputSpec):
    pipelines = List(Dict(), mandatory=True)
    tasks = List(Str(), mandatory=True)
    output_dir = Directory(exists=True)
    sessions = List(Str(), mandatory=False)
    runs = List(Str(), mandatory=False)

    excluded_subjects = List(Dict(
        desc="Dictionary with all relevant entities key-value pairs and field 'excluded_subjects'"
             "with value of list of strings for each excluded subject"
    ), value=[])

    warnings = List(Dict(
        desc="Dictionary with all relevant entities key-value pairs and field 'warnings'"
             "with value of list of strings for each warning message"
    ), value=[])
    
    # Aggregated over pipelines
    plots_all_pipelines_edges_density = List(File(
        exists=True,
        desc="Density of edge weights (all pipelines) for all subjects"
    ))

    plots_all_pipelines_edges_density_no_high_motion = List(File(
        exists=True,
        desc="Density of edge weights (all pipelines) without high motion subjects"
    ))

    plots_all_pipelines_fc_fd_pearson_info = List(File(
        exists=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values for all subjects"
    ))

    plots_all_pipelines_fc_fd_pearson_info_no_high_motion = List(File(
        exists=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values without high motion subjects"
    ))

    plots_all_pipelines_distance_dependence = List(File(
        exists=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs for all subject"
    ))

    plots_all_pipelines_distance_dependence_no_high_motion = List(File(
        exists=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs without high motion subjects"
    ))

    plots_all_pipelines_tdof_loss = List(File(
        exists=True,
        desc="Barplot showing degree of freedom loss (number of regressors included in each pipeline."
    ))

    # For single pipeline
    plots_pipeline_fc_fd_pearson_matrix = List(File(
        exists=True,
        desc="Matrix showing correlation between connection strength and motion for all subjects"
    ))

    plots_pipeline_fc_fd_pearson_matrix_no_high_motion = List(File(
        exists=True,
        desc="Matrix showing correlation between connection strength and motion without high motion subjects"
    ))


class ReportCreator(SimpleInterface):
    input_spec = ReportCreatorInputSpec

    def _run_interface(self, runtime):
        # Find all distinct entities
        plots_all_pipelines, plots_pipeline = {}, {}
        for plots_type, plots_list in self.inputs.__dict__.items():
            
            if (plots_type.startswith('plots_all_pipelines') 
                and isinstance(plots_list, list)):
                plots_all_pipelines[plots_type] = plots_list

            if (plots_type.startswith('plots_pipeline') 
                and isinstance(plots_list, list)):
                plots_pipeline[plots_type] = plots_list
                
        unique_entities = set(
                map(lambda path: frozendict(filter(
                       lambda pair: pair[0] in ['session', 'task', 'run'],
                       parse_file_entities(path).items())),
                    chain(*chain(plots_all_pipelines.values(), plots_pipeline.values()))))

        unique_pipelines = set(pipeline['name'] for pipeline in self.inputs.pipelines)
        # Create input for create_report
        figures_dir = Path(self.inputs.output_dir).joinpath('figures')
        figures_dir.mkdir(parents=True, exist_ok=True)
        report_data = []

        for entity in unique_entities:
            
            entity_data = {
                'entity_name': build_path(entity, "[ses-{session}] task-{task} [run-{run}]"),
                'entity_id': build_path(entity, "[ses-{session}-]task-{task}[-run-{run}]")
            }

            # Manage plots for all_pipelines
            for plots_type, plots_list in plots_all_pipelines.items():
                for plot in plots_list:
                    if is_entity_subset(parse_file_entities(plot), entity):
                        plot_basename = os.path.basename(plot)
                        plot_relative_path = os.path.join('figures', plot_basename)
                        copyfile(plot, os.path.join(figures_dir, plot_basename))
                        entity_data[plots_type] = plot_relative_path
                        break

            # Manage plots for single pipeline
            entity_data['pipeline'] = []
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
                        if pipeline in plot and is_entity_subset(parse_file_entities(plot), entity):
                            plot_basename = os.path.basename(plot)
                            plot_relative_path = os.path.join('figures', plot_basename)
                            copyfile(plot, os.path.join(figures_dir, plot_basename))
                            pipeline_data[plots_type] = plot_relative_path

                # append new pipeline data dict
                entity_data['pipeline'].append(pipeline_data)

            # append new entity data dict
            report_data.append(entity_data)
           
        # Create report
        create_report(
            report_data, 
            output_dir=self.inputs.output_dir,
            report_name='fMRIdenoise_report.html'
            )

        return runtime
