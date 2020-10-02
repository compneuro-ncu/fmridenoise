import os
import pathlib

from fmridenoise.interfaces.report_creator import ReportCreator
from fmridenoise.pipelines import load_pipeline_from_json

from .utils import create_dummy_plots

if __name__ == '__main__':
    
    # Prepare paths
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = 'dummy_report'
    report_dir = os.path.join(cur_dir, output_dir)
    pathlib.Path(os.path.join(report_dir, 'tmp')).mkdir(parents=True, exist_ok=True)
    
    # Setup entities and pipelines
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
    pipelines = []
    for pipeline_file in pipelines_dict.values():
        pipelines.append(
            load_pipeline_from_json(
                os.path.join('fmridenoise/pipelines', pipeline_file)
                )
            )
    # Input arguments for ReportCreator interface    
    plots_dict = create_dummy_plots(
        entity_list=entity_list,
        pipeline_dict=pipelines_dict,
        path_out=os.path.join(report_dir, 'tmp')
    )

    # Create & run interface
    interface = ReportCreator(
        pipelines=pipelines,
        tasks=['rest', 'tapping'],
        sessions=['ses-1', 'ses-2'],
        output_dir=report_dir, 
        **plots_dict
    )
    interface.run()
