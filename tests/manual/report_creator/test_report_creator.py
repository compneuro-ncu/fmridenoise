import os
import pathlib
import pprint

import matplotlib.pyplot as plt
import numpy as np

from fmridenoise.pipelines import load_pipeline_from_json
from fmridenoise.utils.report_creator import create_report


def stringify_entity(entity_dict):
    if 'ses' not in entity_dict:
        return f'task-{entity_dict["task"]}'
    else:
        return f'task-{entity_dict["task"]}_ses-{entity_dict["ses"]}'

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

    plot_names_all_pipelines = [
        'plot_all_pipelines_edges_density', 
        'plot_all_pipelines_edges_density_no_high_motion',
        'plot_all_pipelines_fc_fd_pearson_info',
        'plot_all_pipelines_fc_fd_pearson_info_no_high_motion',
        'plot_all_pipelines_distance_dependence',
        'plot_all_pipelines_distance_dependence_no_high_motion',
        'plot_all_pipelines_tdof_loss'
        ]

    plot_names_pipeline = [
        'plot_pipeline_fc_fd_pearson_matrix',
        'plot_pipeline_fc_fd_pearson_matrix_no_high_motion'
    ]

    plots_dict = {plot_name: [] for 
                 plot_name in plot_names_all_pipelines + plot_names_pipeline}

    for entity in entity_list:

        # All pipelines
        for plot_name in plot_names_all_pipelines:

            fig, ax = plt.subplots(figsize=(12, 7))
            ax.text(0.5, 0.6, stringify_entity(entity), 
                    horizontalalignment='center', verticalalignment='center',
                    fontSize=fontSize)
            ax.text(0.5, 0.4, plot_name, 
                    horizontalalignment='center', verticalalignment='center',
                    fontSize=fontSize)

            path_full = os.path.join(
                path_out, stringify_entity(entity) + '_' + plot_name + '.svg')
            plots_dict[plot_name].append(path_full)

            fig.savefig(path_full)
            plt.close('all')

        # Single pipeline
        for plot_name in plot_names_pipeline:
            for pipeline in pipeline_dict:

                fig, ax = plt.subplots(figsize=(10, 10))
                ax.imshow(np.random.random((100, 100)))
                ax.set_title(stringify_entity(entity) + ' ' + plot_name, 
                             fontSize=fontSize)
                ax.set_ylabel(pipeline, fontSize=fontSize)

                path_full = os.path.join(path_out, 
                    stringify_entity(entity) + f'_{pipeline}_' \
                    + plot_name + '.svg')
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

if __name__ == "__main__":

    cur_dir = os.path.dirname(os.path.realpath(__file__))

    ##########
    # Test 1 #
    ##########
    output_dir = 'dummy_report_1'
    report_dir = os.path.join(cur_dir, output_dir)
    pathlib.Path(os.path.join(report_dir, 'dummy_plots')).mkdir(parents=True, 
                                                                exist_ok=True)

    entity_list = [
        {'task': 'rest', 'ses': '1'}, 
        {'task': 'rest', 'ses': '2'}, 
        {'task': 'tapping', 'ses': '1'},
        ]

    pipelines_dict = {
        'Null': 'pipeline-Null.json', 
        '24HMP8PhysSpikeReg': 'pipeline-24HMP_8Phys_SpikeReg.json', 
        'ICAAROMA8Phys': 'pipeline-ICA-AROMA_8Phys.json'
        }

    # Interface inputs
    pipelines = [
        load_pipeline_from_json(os.path.join('fmridenoise/pipelines', pipeline)) 
        for pipeline in pipelines_dict.values()
        ]
    plots_dict = create_dummy_plots(
        entity_list, pipelines_dict.keys(), 
        os.path.join(cur_dir, output_dir, 'dummy_plots')
        )
    
    # Simulating interface internal work
    report_data = create_report_data(entity_list, pipelines_dict, plots_dict)
    
    # Create report
    create_report(report_data, report_dir)

    ##########
    # Test 2 #
    ##########
    output_dir = 'dummy_report_2'
    report_dir = os.path.join(cur_dir, output_dir)
    pathlib.Path(os.path.join(report_dir, 'dummy_plots')).mkdir(parents=True, 
                                                                exist_ok=True)

    entity_list = [
        {'task': 'myTask1'}, 
        {'task': 'myTask2'},
        ]

    pipelines_dict = {
        '24HMPaCompCorSpikeReg4GSR': 'pipeline-24HMP_aCompCor_SpikeReg_4GS.json', 
        }

    # Interface inputs
    pipelines = [
        load_pipeline_from_json(os.path.join('fmridenoise/pipelines', pipeline)) 
        for pipeline in pipelines_dict.values()
        ]
    plots_dict = create_dummy_plots(
        entity_list, pipelines_dict.keys(), 
        os.path.join(cur_dir, output_dir, 'dummy_plots')
        )
    
    # Simulating interface internal work
    report_data = create_report_data(entity_list, pipelines_dict, plots_dict)
    
    # Create report
    create_report(report_data, report_dir)
