from nipype.pipeline import engine as pe

from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink
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
                        ica_aroma=True,
                        high_pass=0.008,
                        low_pass=0.08,
                        # desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir='/tmp/fmridenoise', name='fmridenoise_wf'
                        ):
    workflow = pe.Workflow(name=name, base_dir=base_dir)
    temps.base_dir = base_dir

    # 1) --- Selecting pipeline

    # Inputs: fulfilled
    pipelineselector = pe.Node(
       PipelineSelector(),
       name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline, pipeline_name, low_pass, high_pass

    # 2) --- Loading BIDS structure

    # Inputs: directory, task, derivatives
    grabbing_bids = pe.Node(
        BIDSGrab(
            bids_dir=bids_dir,
            derivatives=derivatives,
            task=task,
            session=session,
            subject=subject,
            ica_aroma=ica_aroma
        ),
        name="BidsGrabber")
    # Outputs: fmri_prep, conf_raw, conf_json, entities, tr_dict

    # 3) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw, conf_json
    prep_conf = pe.MapNode(
        Confounds(
            output_dir=temps.mkdtemp('prep_conf')
        ),
        iterfield=['conf_raw', 'conf_json', 'entities'],
        name="ConfPrep")
    # Outputs: conf_prep, low_pass, high_pass

    # 4) --- Denoising

    # Inputs: conf_prep, low_pass, high_pass
    denoise = pe.MapNode(
        Denoise(
            smoothing=smoothing,
            high_pass=high_pass,
            low_pass=low_pass,
            ica_aroma=ica_aroma,
            output_dir=temps.mkdtemp('denoise')
        ),
        iterfield=['fmri_prep', 'fmri_prep_aroma', 'conf_prep', 'entities'],
        name="Denoiser", mem_gb=6)

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
        (grabbing_bids, denoise, [('tr_dict', 'tr_dict')]),
        (grabbing_bids, denoise, [('fmri_prep', 'fmri_prep'),
                                  ('fmri_prep_aroma', 'fmri_prep_aroma')]),
        (grabbing_bids, denoise, [('entities', 'entities')]),
        (grabbing_bids, prep_conf, [('conf_raw', 'conf_raw'),
                                    ('conf_json', 'conf_json'),
                                    ('entities', 'entities')]),
        (grabbing_bids, ds_confounds, [('entities', 'entities')]),
        (grabbing_bids, ds_denoise, [('entities', 'entities')]),
        (grabbing_bids, ds_connectivity, [('entities', 'entities')]),
        (grabbing_bids, ds_carpet_plot, [('entities', 'entities')]),
        (grabbing_bids, ds_matrix_plot, [('entities', 'entities')]),

        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (pipelineselector, denoise, [('pipeline', 'pipeline')]),
        (prep_conf, group_conf_summary, [('conf_summary', 'conf_summary'),
                                        ('pipeline_name', 'pipeline_name')]),

        (pipelineselector, ds_denoise, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_connectivity, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_confounds, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_carpet_plot, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_matrix_plot, [('pipeline_name', 'pipeline_name')]),

        (prep_conf, denoise, [('conf_prep', 'conf_prep')]),
        (denoise, connectivity, [('fmri_denoised', 'fmri_denoised')]),

        (prep_conf, group_connectivity, [('pipeline_name', 'pipeline_name')]),
        (connectivity, group_connectivity, [('corr_mat', 'corr_mat')]),

        (prep_conf, ds_confounds, [('conf_prep', 'in_file')]),
        (denoise, ds_denoise, [('fmri_denoised', 'in_file')]),
        (connectivity, ds_connectivity, [('corr_mat', 'in_file')]),
        (connectivity, ds_carpet_plot, [('carpet_plot', 'in_file')]),
        (connectivity, ds_matrix_plot, [('matrix_plot', 'in_file')]),

        (group_connectivity, quality_measures, [('pipeline_name', 'pipeline_name'),
                                                ('group_corr_mat', 'group_corr_mat')]),
        (group_conf_summary, quality_measures, [('group_conf_summary', 'group_conf_summary')]),
        (quality_measures, merge_quality_measures, [('fc_fd_summary', 'fc_fd_summary'),
                                                    ('edges_weight', 'edges_weight'),
                                                    ('edges_weight_clean', 'edges_weight_clean'),
                                                    ('exclude_list', 'exclude_list')]),
        (merge_quality_measures, pipelines_quality_measures,
            [('fc_fd_summary', 'fc_fd_summary'),
             ('edges_weight', 'edges_weight'),
             ('edges_weight_clean', 'edges_weight_clean')]),
        (merge_quality_measures, report_creator,
            [('exclude_list', 'excluded_subjects')]),
        (pipelines_quality_measures, report_creator,
            [('plot_pipeline_edges_density', 'plot_pipeline_edges_density'),
             ('plot_pipelines_edges_density_no_high_motion', 'plot_pipelines_edges_density_no_high_motion'),
             ('plot_pipelines_fc_fd_pearson', 'plot_pipelines_fc_fd_pearson'),
             ('plot_pipelines_fc_fd_uncorr', 'plot_pipelines_fc_fd_uncorr'),
             ('plot_pipelines_distance_dependence', 'plot_pipelines_distance_dependence')]),
        (pipelineselector, report_creator,
            [('pipeline', 'pipelines'),
             ('pipeline_name', 'pipelines_names')])
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
