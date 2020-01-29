from nipype.pipeline import engine as pe
from nipype import Node, IdentityInterface
from fmridenoise.interfaces.smoothing import Smooth
from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink, BIDSValidate
from fmridenoise.interfaces.confounds import Confounds, GroupConfounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity, GroupConnectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector
from fmridenoise.interfaces.quality_measures import QualityMeasures, PipelinesQualityMeasures, MergeGroupQualityMeasures
from fmridenoise.interfaces.report_creator import ReportCreator
import fmridenoise.utils.temps as temps
from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path
from fmridenoise.pipelines import get_pipelines_paths
import os
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
    pipelines_paths = list(pipelines_paths)
    bids_validate = Node(BIDSValidate(bids_dir=bids_dir,
                               derivatives=derivatives,
                               tasks=task,
                               sessions=session,
                               subjects=subject,
                               pipelines=pipelines_paths),
                         name='BidsValidate')
    result = bids_validate.run()

    temps.base_dir = base_dir
    workflow = pe.Workflow(name=name, base_dir=base_dir)
    # 1) --- Itersources for all further processing

    # Inputs: fulfilled
    pipelineselector = Node(
       PipelineSelector(),
       name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline, pipeline_name, low_pass, high_pass

    # Inputs: fulfilled
    subjectselector = Node(
        IdentityInterface(
            fields=['subject']),
        name="SubjectSelector")
    subjectselector.iterables = ('subject', result.outputs.subjects)
    # Outputs: subject

    # Inputs: fulfilled
    taskselector = Node(
        IdentityInterface(
            fields=['task']),
        name="TaskSelector")
    taskselector.iterables = ('task', result.outputs.tasks)
    # Outputs: task

    # Inputs: fulfilled
    sessionselector = Node(
        IdentityInterface(
            fields=['session']),
        name="SessionSelector")
    sessionselector.iterables = ('session', result.outputs.sessions)
    # Outputs: session

    # 2) --- Loading BIDS files

    # Inputs: subject, session, task
    bidsgrabber = Node(
        BIDSGrab(
            fmri_prep_files=result.outputs.fmri_prep,
            fmri_prep_aroma_files=result.outputs.fmri_prep_aroma,
            conf_raw_files=result.outputs.conf_raw,
            conf_json_files=result.outputs.conf_json),
        name="BidsGrabber")
    # Outputs: fmri_prep, fmri_prep_aroma, conf_raw, conf_json

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
    # Outputs: conf_prep, conf_summary

    

    # 4) --- Denoising
    # Inputs: fmri_prep, fmri_prep_aroma, conf_prep, pipeline, entity, tr_dict
    denoise = Node(
        Denoise(
            high_pass=high_pass,
            low_pass=low_pass,
            tr_dict=result.outputs.tr_dict,
            output_dir=temps.mkdtemp('denoise')),
        name="Denoiser", 
        mem_gb=6)
    # Outputs: fmri_denoised

    # 5) --- Connectivity estimation

    # Inputs: fmri_denoised
    parcellation_path = get_parcelation_file_path()
    connectivity = Node(
        Connectivity(
            output_dir=temps.mkdtemp('connectivity'),
            parcellation=parcellation_path
        ),
        name='ConnCalc')
    # Outputs: conn_mat, carpet_plot

    # 6) --- Group confounds

    # Inputs: conf_summary, pipeline_name
    # FIXME BEGIN
    # This is part of temporary solution.
    # Group nodes write to bids dir insted of tmp and let files be grabbed by datasink
    os.makedirs(os.path.join(bids_dir, 'derivatives', 'fmridenoise'), exist_ok=True)
    # FIXME END
    group_conf_summary = pe.JoinNode(
        GroupConfounds(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
        ),
        joinfield=["conf_summary_json_files"],
        joinsource=subjectselector,
        name="GroupConf")

    # Outputs: group_conf_summary

    # 7) --- Group connectivity

    # Inputs: corr_mat, pipeline_name

    group_connectivity = pe.JoinNode(
        GroupConnectivity(
            output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
        ),
        joinfield=["corr_mat"],
        joinsource=subjectselector,
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
    ds_confounds = Node(BIDSDataSink(base_directory=bids_dir),
                    name="ds_confounds")

    ds_denoise = Node(BIDSDataSink(base_directory=bids_dir),
                    name="ds_denoise")

    ds_connectivity_corr_mat = Node(BIDSDataSink(base_directory=bids_dir),
                    name="ds_connectivity")

    ds_connectivity_carpet_plot = Node(BIDSDataSink(base_directory=bids_dir),
                                 name="ds_carpet_plot")

    ds_connectivity_matrix_plot = Node(BIDSDataSink(base_directory=bids_dir),
                                 name="ds_matrix_plot")


# --- Connecting nodes

    workflow.connect([
        # bidsgrabber
        (sessionselector, bidsgrabber, [('session', 'session')]),
        (subjectselector, bidsgrabber, [('subject', 'subject')]),
        (taskselector, bidsgrabber, [('task', 'task')]),
        # smooth_signal
        (bidsgrabber, smooth_signal, [('fmri_prep', 'fmri_prep')]),
        # prep_conf
        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (subjectselector, prep_conf, [('subject', 'subject')]),
        (taskselector, prep_conf, [('task', 'task')]),
        (sessionselector, prep_conf, [('session', 'session')]),
        (bidsgrabber, prep_conf, [('conf_raw', 'conf_raw'), 
                                  ('conf_json', 'conf_json')]),
        # denoise
        (smooth_signal, denoise, [('fmri_smoothed', 'fmri_prep')]),
        (prep_conf, denoise, [('conf_prep', 'conf_prep')]),
        (pipelineselector, denoise, [('pipeline', 'pipeline')]),
        (bidsgrabber, denoise, [('fmri_prep_aroma', 'fmri_prep_aroma')]),
        (taskselector, denoise, [('task', 'task')]),
        # group conf summary
        (prep_conf, group_conf_summary, [('conf_summary_json_file', 'conf_summary_json_files')]),
        (sessionselector, group_conf_summary, [('session', 'session')]),
        (taskselector, group_conf_summary, [('task', 'task')]),
        (pipelineselector, group_conf_summary, [('pipeline_name', 'pipeline_name')]),
        # connectivity
        (denoise, connectivity, [('fmri_denoised', 'fmri_denoised')]),
        # group connectivity
        (connectivity, group_connectivity, [("corr_mat", "corr_mat")]),
        (pipelineselector, group_connectivity, [("pipeline_name", "pipeline_name")]),
        (taskselector, group_connectivity, [('task', 'task')]),
        (sessionselector, group_connectivity, [('session', 'session')]),
        # quality measures

        # all datasinks
        ## ds_denoise
        (subjectselector, ds_denoise, [("subject", "subject")]),
        (sessionselector, ds_denoise, [("session", "session")]),
        (denoise, ds_denoise, [("fmri_denoised", "in_file")]),
        ## ds_connectivity
        (subjectselector, ds_connectivity_corr_mat, [("subject", "subject")]),
        (sessionselector, ds_connectivity_corr_mat, [("session", "session")]),
        (connectivity, ds_connectivity_corr_mat, [("corr_mat", "in_file")]),
        (subjectselector, ds_connectivity_matrix_plot, [("subject", "subject")]),
        (sessionselector, ds_connectivity_matrix_plot, [("session", "session")]),
        (connectivity, ds_connectivity_matrix_plot, [("matrix_plot", "in_file")]),
        (subjectselector, ds_connectivity_carpet_plot, [("subject", "subject")]),
        (sessionselector, ds_connectivity_carpet_plot, [("session", "session")]),
        (connectivity, ds_connectivity_carpet_plot, [("carpet_plot", "in_file")]),
        ## ds_confounds
        (subjectselector, ds_confounds, [("subject", "subject")]),
        (sessionselector, ds_confounds, [("session", "session")]),
        (prep_conf, ds_confounds, [("conf_prep", "in_file")]),
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
