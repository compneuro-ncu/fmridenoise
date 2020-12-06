import os
import pathlib
import sys
from functools import reduce

from fmridenoise._version import get_versions
from fmridenoise.interfaces.report_creator import ReportCreator
from fmridenoise.pipelines import load_pipeline_from_json, get_pipeline_path
from fmridenoise.utils.error_data import ErrorData
from fmridenoise.utils.runtime_info import RuntimeInfo

from .utils import create_dummy_plots

if __name__ == '__main__':
    
    # Prepare paths
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    output_dir = 'dummy_report'
    report_dir = os.path.join(cur_dir, output_dir)
    pathlib.Path(os.path.join(report_dir, 'tmp')).mkdir(parents=True, exist_ok=True)
    
    # Setup entities and pipelines
    entity_list = [
        {'task': 'rest', 'session': '1', 'run': 1},
        {'task': 'rest', 'session': '2', 'run': 1},
        {'task': 'tapping', 'session': '1', 'run': 1},
        {'task': 'rest', 'session': '1', 'run': 2},
        {'task': 'rest', 'session': '2', 'run': 2},
        {'task': 'tapping', 'session': '1', 'run': 2}
        ]
    pipelines_dict = {
        'Null': 'pipeline-Null',
        '24HMP8PhysSpikeReg': 'pipeline-24HMP_8Phys_SpikeReg',
        'ICAAROMA8Phys': 'pipeline-ICA-AROMA_8Phys'
        }
    error_source = object()
    warnings = [
        ErrorData.error(
            {'task': 'rest', 'session': '1', 'run': 1, 'pipeline': 'Null'},
            source=error_source,
            message="Error message 1"),
        ErrorData.error(
            {'task': 'rest', 'session': '1', 'run': 1, 'pipeline': 'Null'},
            source=error_source,
            message="Error message 2"),
        ErrorData.warning(
            {'task': 'rest', 'session': '1', 'run': 1, 'pipeline': 'Null'},
            source=error_source,
            message="Warning message 1")
    ]
    excluded_subjects = [
        {'task': 'rest', 'session': '1', 'run': 1, 'excluded': ['sub-1', 'sub-2', 'sub-3']},
        {'task': 'rest', 'session': '1', 'run': 2, 'excluded': ['sub-1', 'sub-2', 'sub-3']},
    ]
    pipelines = []
    for pipeline_name in pipelines_dict.values():
        pipelines.append(
            load_pipeline_from_json(
                get_pipeline_path(pipeline_name)
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
        runtime_info=RuntimeInfo(
            input_args=str(reduce(lambda x, y: f"{x} {y}", sys.argv)),
            version=get_versions().get('version')
        ),
        pipelines=pipelines,
        tasks=['rest', 'tapping'],
        sessions=['1', '2'],
        runs=[1, 2],
        output_dir=report_dir,
        warnings=warnings,
        excluded_subjects=excluded_subjects,
        **plots_dict
    )
    interface.run()
