import os
from collections import namedtuple

from nipype.interfaces.base import BaseInterfaceInputSpec, SimpleInterface
from traits.trait_types import Dict, Directory, File, List, Str

from fmridenoise.utils.entities import parse_file_entities_with_pipelines
from fmridenoise.utils.report_creator import create_report
from fmridenoise.pipelines import load_pipeline_from_json

class ReportCreatorInputSpec(BaseInterfaceInputSpec):
    pipelines = List(Dict(), mandatory=True)
    tasks = List(Str(), mandatory=True)
    sessions = List(Str(), mandatory=False)    
    output_dir = Directory(exists=True)

    # excluded_subjects = List(Str(), value=()) # TODO: This mayby another input field later. 
    
    # Aggregated over pipelines
    plots_all_pipelines_edges_density = List(File(
        #exists=True,
        desc="Density of edge weights (all pipelines) for all subjects"
    ))

    plots_all_pipelines_edges_density_no_high_motion = List(File(
        #exist=True,
        desc="Density of edge weights (all pipelines) without high motion subjects"
    ))

    plots_all_pipelines_fc_fd_pearson_info = List(File(
        exist=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values for all subjects"
    ))

    plots_all_pipelines_fc_fd_pearson_info_no_high_motion = List(File(
        exist=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values without high motion subjects"
    ))

    plots_all_pipelines_distance_dependence = List(File(
        exist=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs for all subject"
    ))

    plots_all_pipelines_distance_dependence_no_high_motion = List(File(
        exist=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs without high motion subjects"
    ))

    plots_all_pipelines_tdof_loss = List(File(
        exists=True,
        desc="..."
    ))

    # For single pipeline
    plots_pipeline_fc_fd_pearson_matrix = List(File(
        exist=True,
        desc="Matrix showing correlation between connection strength and motion for all subjects"
    ))

    plots_pipeline_fc_fd_pearson_matrix_no_high_motion = List(File(
        exist=True,
        desc="Matrix showing correlation between connection strength and motion without high motion subjects"
    ))


# List with structured dictionaries for each entity.
#
# Dictionary keys and values:
#     'entity_name': 
#         Name of task / task+session entity used to name the report tab.
#     'entity_id':
#         Id of task / task+session entity used for html elements id.
#     'plots_all_pipelines_<plot_name>': 
#         Path for plot aggregating pipelines.
#     'pipeline'
#         List of dicts for each pipeline. Each pipeline dictionary has 
#         key, value pairs:
    
#         'pipeline_dict':
#             Parsed pipeline JSON.
#         'plots_pipeline_<plot_name>':
#             Path for plot for single pipeline.

class ReportCreator(SimpleInterface):
    input_spec = ReportCreatorInputSpec

    @staticmethod
    def entity_tuple_from_dict(entity_dict):
        
        EntityTuple = namedtuple('EntityTuple', 'task session')

        if 'session' in entity_dict:
            return EntityTuple(entity_dict['task'], entity_dict['session'])
        else:
            return EntityTuple(entity_dict['task'], None)

    @staticmethod
    def entity_tuple_to_entity_name(entity_tuple):
        '''Converts into name of task / task+session entity used for the report 
        tab title.'''
        if entity_tuple.session is None:
            return f'task-{entity_tuple.task}'
        else:
            return f'task-{entity_tuple.task} ses-{entity_tuple.session}'

    @staticmethod
    def entity_tuple_to_entity_id(entity_tuple):
        '''Converts into id of task / task+session entity used for html elements 
        id.'''
        if entity_tuple.session is None:
            return f'task-{entity_tuple.task}'
        else:
            return f'task-{entity_tuple.task}-ses-{entity_tuple.session}'

    def _run_interface(self, runtime):

        # Find all distinct entities
        plots_all_pipelines, plots_pipeline = [], []
        for plots_type, plots_list in self.inputs.__dict__.items():
            
            if plots_type.startswith('plots_all_pipelines') and isinstance(plots_list, list):
                plots_all_pipelines.extend(plots_list)

            if plots_type.startswith('plots_pipeline') and isinstance(plots_list, list):
                plots_pipeline.extend(plots_list)
                
        unique_entities = set(
            map(self.entity_tuple_from_dict, 
                map(parse_file_entities_with_pipelines,
                    plots_all_pipelines + plots_pipeline)))

        unique_pipelines = set(
            map(lambda dict_: dict_['pipeline'], 
                map(parse_file_entities_with_pipelines,
                    plots_pipeline)))

        # Create input for create_report
        figures_dir = os.path.join(self.inputs.output_dir, 'figures')
        report_data = []

        for entity_tuple in unique_entities:

            entity_data = {
                'entity_name': self.entity_tuple_to_entity_name(entity_tuple),
                'entity_id': self.entity_tuple_to_entity_id(entity_tuple),
            }

            for plots_type, plots_list in self.inputs.__dict__.items():
                
                if (plots_type.startswith('plots_all_pipeline') 
                    and isinstance(plots_list, list)):
            
                    entity_data[plots_type] = next(
                        os.path.join(figures_dir, os.path.basename(plot_path)) 
                        for plot_path in plots_list
                        if self.entity_tuple_from_dict(parse_file_entities_with_pipelines(plot_path)) == entity_tuple
                    )

                if (plots_type.startswith('plots_pipeline') 
                    and isinstance(plots_list, list)):

                    pipeline_data = []

                    for pipeline_name in unique_pipelines:
                        
                        # Get pipeline dict
                        pipeline_dict = next(
                            pipeline_dict 
                            for pipeline_dict in self.inputs.pipelines 
                            if pipeline_dict['name'] == pipeline_name 
                        )

                        # Get pipeline plots
                        pipeline_plots = {}
                        for plots_type, plots_list in self.inputs.__dict__.items():                               
                            
                            if (plots_type.startswith('plots_pipeline') 
                                and isinstance(plots_list, list)):
                        
                                for plot_path in plots_list:

                                    entity_dict = parse_file_entities_with_pipelines(plot_path)
                                    
                                    if self.entity_tuple_from_dict(entity_dict) == entity_tuple:

                                        print(entity_dict) 
                                    

                        pipeline_data.append({'pipeline_dict': pipeline_name, **pipeline_plots}) 
                   
                    entity_data['pipeline'] = pipeline_data

            report_data.append(entity_data)

        

        import pprint
        pprint.pprint(report_data)

        return runtime

if __name__ == '__main__':


    plots_all_pipelines_edges_density = [
        '/tmp/task-rest_ses-1_desc-edgesDensity_plot.svg',
        '/tmp/task-rest_ses-2_desc-edgesDensity_plot.svg',
    ]
    plots_all_pipelines_edges_density_no_high_motion = [
        '/tmp/task-rest_ses-1_desc-edgesDensityNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-2_desc-edgesDensityNoHighMotion_plot.svg',
    ]    
    plots_pipeline_fc_fd_pearson_matrix = [
        '/tmp/task-rest_ses-1_pipeline-Null_desc-fcFdPearsonMatrix_plot.svg',
        '/tmp/task-rest_ses-1_pipeline-24HMPaCompCorSpikeReg_desc-fcFdPearsonMatrix_plot.svg',
        '/tmp/task-rest_ses-1_pipeline-ICAAROMA8Phys_desc-fcFdPearsonMatrix_plot.svg',
        '/tmp/task-rest_ses-2_pipeline-Null_desc-fcFdPearsonMatrix_plot.svg',
        '/tmp/task-rest_ses-2_pipeline-24HMPaCompCorSpikeReg_desc-fcFdPearsonMatrix_plot.svg'
        '/tmp/task-rest_ses-2_pipeline-ICAAROMA8Phys_desc-fcFdPearsonMatrix_plot.svg'
    ]
    plots_pipeline_fc_fd_pearson_matrix_no_high_motion = [
        '/tmp/task-rest_ses-1_pipeline-Null_desc-fcFdPearsonMatrixNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-1_pipeline-24HMPaCompCorSpikeReg_desc-fcFdPearsonMatrixNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-1_pipeline-ICAAROMA8Phys_desc-fcFdPearsonMatrixNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-2_pipeline-Null_desc-fcFdPearsonMatrixNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-2_pipeline-24HMPaCompCorSpikeReg_desc-fcFdPearsonMatrixNoHighMotion_plot.svg',
        '/tmp/task-rest_ses-2_pipeline-ICAAROMA8Phys_desc-fcFdPearsonMatrixNoHighMotion_plot.svg'
    ]    

    pipelines = [
        load_pipeline_from_json(json_path) for json_path in (
            'fmridenoise/pipelines/pipeline-Null.json',
            'fmridenoise/pipelines/pipeline-ICA-AROMA_8Phys.json',
            'fmridenoise/pipelines/pipeline-24HMP_aCompCor_SpikeReg.json'
        )
        ]

    interface = ReportCreator(
        pipelines=pipelines,
        tasks=[''],
        sessions=[''],
        output_dir='/var',
        plots_all_pipelines_edges_density=plots_all_pipelines_edges_density,
        plots_all_pipelines_edges_density_no_high_motion=plots_all_pipelines_edges_density_no_high_motion,
        plots_pipeline_fc_fd_pearson_matrix=plots_pipeline_fc_fd_pearson_matrix,
        plots_pipeline_fc_fd_pearson_matrix_no_high_motion=plots_pipeline_fc_fd_pearson_matrix_no_high_motion
    )  
    interface.run()
