from nipype.pipeline import engine as pe
from nipype import Node, SelectFiles, IdentityInterface, Function
from fmridenoise.interfaces.smoothing import Smooth
from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink, BIDSSelect
from fmridenoise.interfaces.confounds import Confounds, GroupConfounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity, GroupConnectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector
from fmridenoise.interfaces.quality_measures import QualityMeasures, PipelinesQualityMeasures, MergeGroupQualityMeasures
from fmridenoise.interfaces.report_creator import ReportCreator
import fmridenoise.utils.temps as temps
from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path

from nipype import config
import fmridenoise
import os
import glob
from fmridenoise.pipelines import get_pipelines_paths

import logging
logger = logging.getLogger("runtime")
handler = logging.FileHandler("./runtime.log")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def init_fmridenoise_wf(bids_dir,
                        derivatives='fmriprep',
                        task=[],
                        session=[],
                        subject=[],
                        pipelines_paths=get_pipelines_paths(),
                        smoothing=True,
                        #ica_aroma=False, TODO: delete this later
                        high_pass=0.008,
                        low_pass=0.08,
                        base_dir='/tmp/fmridenoise', 
                        name='fmridenoise_wf'):

    bids_select = BIDSSelect(bids_dir=bids_dir,
                             derivatives=derivatives,
                             task=task,
                             session=session,
                             subject=subject,
                             ica_aroma=ica_aroma)
    workflow = pe.Workflow(name=name, base_dir=base_dir)
    temps.base_dir = base_dir

    # 1) --- Itersources for all further processing

    # Inputs: fulfilled
    pipelineselector = pe.Node(
       PipelineSelector(),
       name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline, pipeline_name, low_pass, high_pass

    # Inputs: fulfilled
    subjectselector = Node(
        IdentityInterface(
            fields=['subject']),
        name="SubjectSelector")
    subjectselector.iterables = ('subject', bids_select.subject)
    # Outputs: subject

    # Inputs: fulfilled
    taskselector = Node(
        IdentityInterface(
            fields=['task']),
        name="TaskSelector")
    taskselector.iterables = ('task', bids_select.task)
    # Outputs: task

    # Inputs: fulfilled
    sessionselector = Node(
        IdentityInterface(
            fields=['session']),
        name="SessionSelector")
    sessionselector.iterables = ('session', bids_select.session)
    # Outputs: session

    # 2) --- Loading BIDS files

    # Inputs: subject, session, task
    bidsgrabber = Node(
        BIDSGrab(
            layout=bids_select.layout,
            scope=bids_select.scope,
            tr_dict=bids_select.tr_dict),
        name="BidsGrabber")
    # Outputs: fmri_prep, fmri_prep_aroma, conf_raw, conf_json, entity

    # 3) --- Smoothing

    # Inputs: fmri_prep
    smooth_signal = Node(
        Smooth(
            output_directory=temps.mkdtemp('smoothing'),
            is_file_mandatory=False), 
        name="Smoother")
    # Outputs: fmri_smoothed

    # 3) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw, conf_json
    prep_conf = Node(
        Confounds(
            output_dir=temps.mkdtemp('prep_conf')
        ), name="ConfPrep")
    # Outputs: conf_prep, conf_summary, pipeline_name

    

    # 4) --- Denoising
    # Inputs: fmri_prep, fmri_prep_aroma, conf_prep, pipeline, entity, tr_dict
    denoise = Node(
        Denoise(
            high_pass=high_pass,
            low_pass=low_pass,
            tr_dict=bids_select.tr_dict,
            output_dir=temps.mkdtemp('denoise')),
        name="Denoiser", 
        mem_gb=6)
    # Outputs: fmri_denoised

    # 5) --- Connectivity estimation

    # Inputs: fmri_denoised
    parcellation_path = get_parcelation_file_path()
    connectivity = pe.MapNode(
        Connectivity(
            output_dir=temps.mkdtemp('connectivity'),
            parcellation=parcellation_path
        ),
        iterfield=['fmri_denoised'],
        name='ConnCalc')
    # Outputs: conn_mat, carpet_plot

    # 6) --- Group confounds

    # Inputs: conf_summary, pipeline_name
    # FIXME BEGIN
    # This is part of temporary solution.
    # Group nodes write to bids dir insted of tmp and let files be grabbed by datasink
    os.makedirs(os.path.join(bids_dir, 'derivatives', 'fmridenoise'), exist_ok=True)
    # FIXME END
    group_conf_summary = pe.Node(
        GroupConfounds(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
        ),
        name="GroupConf")

    # Outputs: group_conf_summary

    # 7) --- Group connectivity

    # Inputs: corr_mat, pipeline_name

    group_connectivity = pe.Node(
        GroupConnectivity(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
        ),
        name="GroupConn")

    # Outputs: group_corr_mat

    # 8) --- Quality measures

    # Inputs: group_corr_mat, group_conf_summary, pipeline_name

    quality_measures = pe.MapNode(
        QualityMeasures(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
            distance_matrix=get_distance_matrix_file_path()
        ),
        iterfield=['group_corr_mat', 'group_conf_summary'],
        name="QualityMeasures")
    # Outputs: fc_fd_summary, edges_weight, edges_weight_clean

    # 9) --- Merge quality measures into lists for further processing

    # Inputs: fc_fd_summary, edges_weight, edges_weight_clean

    merge_quality_measures = pe.JoinNode(MergeGroupQualityMeasures(),
                                         joinsource=pipelineselector,
                                         name="Merge")

    # Outputs: fc_fd_summary, edges_weight

    # 10) --- Quality measures across pipelines

    # Inputs: fc_fd_summary, edges_weight

    pipelines_quality_measures = pe.Node(
        PipelinesQualityMeasures(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
        ),
        name="PipelinesQC")

    # Outputs: pipelines_fc_fd_summary, pipelines_edges_weight

    # 11) --- Report from data

    report_creator = pe.JoinNode(
        ReportCreator(
            group_data_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise')
        ),
        joinsource=pipelineselector,
        joinfield=['pipelines', 'pipelines_names'],
        name='ReportCreator')

    # 12) --- Save derivatives
    # TODO: Fill missing in/out
    ds_confounds = pe.MapNode(BIDSDataSink(base_directory=bids_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_confounds")

    ds_denoise = pe.MapNode(BIDSDataSink(base_directory=bids_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_denoise")

    ds_connectivity = pe.MapNode(BIDSDataSink(base_directory=bids_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_connectivity")

    ds_carpet_plot = pe.MapNode(BIDSDataSink(base_directory=bids_dir),
                                 iterfield=['in_file', 'entities'],
                                 name="ds_carpet_plot")

    ds_matrix_plot = pe.MapNode(BIDSDataSink(base_directory=bids_dir),
                                 iterfield=['in_file', 'entities'],
                                 name="ds_matrix_plot")


# --- Connecting nodes

    workflow.connect([
        (sessionselector, bidsgrabber, [('session', 'session')]),
        (subjectselector, bidsgrabber, [('subject', 'subject')]),
        (taskselector, bidsgrabber, [('task', 'task')]),
        (bidsgrabber, smooth_signal, [('fmri_prep', 'fmri_prep')]),
        (smooth_signal, denoise, [('fmri_smoothed', 'fmri_prep')]),
        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (bidsgrabber, prep_conf, [('conf_raw', 'conf_raw'), 
                                  ('conf_json', 'conf_json')]),
        (prep_conf, denoise, [('conf_prep', 'conf_prep')]),
        (pipelineselector, denoise, [('pipeline', 'pipeline')]),
        (bidsgrabber, denoise, [('fmri_prep_aroma', 'fmri_prep_aroma'),
                               ('entity', 'entity')])
    ])

    return workflow


# --- TESTING

if __name__ == '__main__':  # TODO Move parser to module __main__

    import argparse
    import os
    import logging

    logging.critical("Please invoke fmridenoise at module level by using: \n \
        python -m fmridenoise \n \
        python fmridenoise \n \
        python ${path_to_directory}/fmridenoise/__main__.py \n \
        This __main__ will be removed soon." )

    parser = argparse.ArgumentParser("Base workflow")
    parser.add_argument("--bids_dir")
    parser.add_argument("--output_dir")
    args = parser.parse_args()

    bids_dir = '/media/finc/Elements/fMRIDenoise_data/BIDS_LearningBrain_short'
    #pipelines_paths={'/home/finc/Dropbox/Projects/fMRIDenoise/fmridenoise/fmridenoise/pipelines/pipeline-24HMP_8Phys_SpikeReg.json'}

    if args.bids_dir is not None:
        bids_dir = args.bids_dir
    if args.output_dir is not None:
        output_dir = args.output_dir

    wf = init_fmridenoise_wf(bids_dir, subject=['01', '02'], task=['rest'], session=['1'], smoothing=True, ica_aroma=True)

    wf.run()
    wf.write_graph("workflow_graph.dot")
