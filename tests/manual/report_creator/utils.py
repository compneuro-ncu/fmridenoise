import os
import matplotlib.pyplot as plt
import numpy as np
from fmridenoise.pipelines import load_pipeline_from_json
from fmridenoise.utils.entities import build_path
import typing as t


def stringify_entity(entity_dict: t.Dict[str, str]):
    pattern = "[ses-{session}_]task-{task}_[run-{run}]-[pipeline-{pipeline}]"
    return build_path(entity_dict, pattern)


def create_dummy_plots(entity_list, pipeline_dict, path_out):
    ''' Creates set of dummy plots as if they came from fmridenoise.

    Args:
        entity_list (list):
            List of dictionaries with either one key 'task' or two keys 'task' 
            and 'sub' describing single denoising entity.
        pipeline dict (dict):
            Dictionary with keys corresponding to pipeline abbreviation used as 
            filename suffixes and values corresponding to 
            pipeline filename (JSON).
        path_out (str):
            Path to save all plots.

    Returns:
        Dictionary with keys corresponding to ReportCreator input variable names
        and values being a list of full paths to figures.
    '''
    fontSize = 16

    plot_names_all_pipelines = {
        'plots_all_pipelines_edges_density': 'edgesDensity', 
        'plots_all_pipelines_edges_density_no_high_motion': 'edgesDensityNoHighMotion',
        'plots_all_pipelines_fc_fd_pearson_info': 'fcFdPearsonInfo',
        'plots_all_pipelines_fc_fd_pearson_info_no_high_motion': 'fcFdPearsonInfoNoHighMotion',
        'plots_all_pipelines_distance_dependence': 'distanceDependence',
        'plots_all_pipelines_distance_dependence_no_high_motion': 'distanceDependenceNoHighMotion',
        'plots_all_pipelines_tdof_loss': 'tDofLoss'
    }

    plot_names_pipeline = {
        'plots_pipeline_fc_fd_pearson_matrix': 'fcFdPearsonMatrix',
        'plots_pipeline_fc_fd_pearson_matrix_no_high_motion': 'fcFdPearsonMatrixNoHighMotion',
    }

    plots_dict = {
        plot_name: [] 
        for plot_name 
        in list(plot_names_all_pipelines.keys()) + list(plot_names_pipeline.keys())
        }

    for entity in entity_list:

        # All pipelines
        for plot_name, plot_abbrev in plot_names_all_pipelines.items():

            fig, ax = plt.subplots(figsize=(12, 7))
            ax.text(0.5, 0.6, stringify_entity(entity), 
                    horizontalalignment='center', verticalalignment='center',
                    fontSize=fontSize)
            ax.text(0.5, 0.4, plot_name, 
                    horizontalalignment='center', verticalalignment='center',
                    fontSize=fontSize)

            path_full = os.path.join(
                path_out, 
                stringify_entity(entity) + \
                f'_desc-{plot_abbrev}' + '_plot.svg'
                )
            plots_dict[plot_name].append(path_full)

            fig.savefig(path_full)
            plt.close('all')

        # Single pipeline
        for plot_name, plot_abbrev in plot_names_pipeline.items():
            for pipeline in pipeline_dict:

                fig, ax = plt.subplots(figsize=(10, 10))
                ax.imshow(np.random.random((100, 100)))
                ax.set_title(stringify_entity(entity) + ' ' + plot_name, 
                             fontSize=fontSize)
                ax.set_ylabel(pipeline, fontSize=fontSize)

                path_full = os.path.join(
                    path_out, 
                    stringify_entity(entity) + \
                    f'_pipeline-{pipeline}' + \
                    f'_desc-{plot_abbrev}' + '_plot.svg'
                    )
                plots_dict[plot_name].append(path_full)

                fig.savefig(path_full)
                plt.close('all')

    return plots_dict


def create_report_data(entity_list, pipelines_dict, plots_dict):
    ''' Creates dict representing all data used for creating reports

    Args:
        entity_list (list):
            List of dictionaries with either one key 'task' or two keys 'task' 
            and 'sub' describing single denoising entity.
        pipeline dict (dict):
            Dictionary with keys corresponding to pipeline abbreviation used as 
            filename suffixes and values corresponding to 
            pipeline filename (JSON).
        plots_dict (dict):
            Dict mimicking the input of the CreateReport interface. Keys 
            correspond to variable names and values correspond to variable 
            values (list of paths).

    Returns:
        List with structured dictionaries for each entity.

        Dictionary keys and values:
            'entity_name': 
                Name of task / task+session entity used to name the report tab.
            'entity_id':
                Id of task / task+session entity used for html elements id.
            'plot_all_pipelines_<plot_name>': 
                Path for plot aggregating pipelines.
            'pipeline'
                List of dicts for each pipeline. Each pipeline dictionary has 
                key, value pairs:
                
                'pipeline_dict':
                    Parsed pipeline JSON.
                'plot_pipeline_<plot_name>':
                    Path for plot for single pipeline.

    Note:
        This functionaly should be reimplemented within ReportCreator interface.
        Output of this function is the only required argument for function 
        generating HTML report.
    '''
    report_data = []

    plots_all_pipelines = {
        k: v for k, v in plots_dict.items() 
        if '_all_pipelines_' in k}
    plots_pipeline = {
        k: v for k, v in plots_dict.items() 
        if '_pipeline_' in k}

    for entity in entity_list:

        # General informations
        if 'ses' in entity:
            entity_data = {
                'entity_name': f'task-{entity["task"]} ses-{entity["ses"]}', 
                'entity_id': f'task-{entity["task"]}-ses-{entity["ses"]}'            
                }
        else:
            entity_data = {
                'entity_name': f'task-{entity["task"]}', 
                'entity_id': f'task-{entity["task"]}'            
                }

        # Plots for all pipelines
        for plot_name, plots_list in plots_all_pipelines.items():

            entity_data[plot_name] = next(filter(
                lambda path: all(v in path for v in entity.values()), 
                plots_list
                ))

        # Plots for single pipeline
        entity_data['pipeline'] = []
        for pipeline, pipeline_file in pipelines_dict.items():

            entity_pipeline_data = {
                'pipeline_dict': load_pipeline_from_json(
                    os.path.join('fmridenoise/pipelines', pipeline_file))
                    }

            for plot_name, plots_list in plots_pipeline.items():

                entity_pipeline_data[plot_name] = next(filter(
                    lambda path: (all(v in path for v in entity.values()) 
                                  and pipeline in path), 
                    plots_list
                    ))

            entity_data['pipeline'].append(entity_pipeline_data)

        report_data.append(entity_data)

    return report_data

