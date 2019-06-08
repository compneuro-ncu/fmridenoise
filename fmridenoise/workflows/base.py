from nipype.pipeline import engine as pe

from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink
from fmridenoise.interfaces.confounds import Confounds, GroupConfounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity, GroupConnectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector
from fmridenoise.interfaces.quality_measures import QualityMeasures, PipelinesQualityMeasures, MergeGroupQualityMeasures
import fmridenoise.utils.temps as temps

import fmridenoise
import os
import glob

def init_fmridenoise_wf(bids_dir,
                        derivatives='fmriprep',
                        task=[],
                        pipelines_paths=glob.glob(os.path.dirname(fmridenoise.__file__) + "/pipelines/*"),
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
            task=task
        ),
        name="BidsGrabber")
    # Outputs: fmri_prep, conf_raw, entities, tr_dict

    # 3) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw
    prep_conf = pe.MapNode(
        Confounds(
            output_dir=temps.mkdtemp('prep_conf')
        ),
        iterfield=['conf_raw', 'entities'],
        name="ConfPrep")
    # Outputs: conf_prep, low_pass, high_pass

    # 4) --- Denoising

    # Inputs: conf_prep, low_pass, high_pass
    denoise = pe.MapNode(
        Denoise(
            output_dir=temps.mkdtemp('denoise')
        ),
        iterfield=['fmri_prep', 'conf_prep', 'entities'],
        name="Denoiser", mem_gb=6)

    # Outputs: fmri_denoised

    # 5) --- Connectivity estimation

    # Inputs: fmri_denoised
    parcellation_path = os.path.abspath(os.path.join(fmridenoise.__path__[0], "parcellation"))
    parcellation_path = glob.glob(parcellation_path + "/*")[0]

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
        ),
        iterfield=['group_corr_mat', 'group_conf_summary'],
        name="QualityMeasures")
    # Outputs: fc_fd_summary, edges_weight

    # 9) --- Merge quality measures into lists for further processing

    # Inputs: fc_fd_summary, edges_weight

    merge_quality_measures = pe.JoinNode(MergeGroupQualityMeasures(),
                                         joinsource=quality_measures,
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

    # 11) --- Save derivatives
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
        (grabbing_bids, denoise, [('fmri_prep', 'fmri_prep')]),
        (grabbing_bids, denoise, [('entities', 'entities')]),
        (grabbing_bids, prep_conf, [('conf_raw', 'conf_raw'),
                                    ('entities', 'entities')]),
        (grabbing_bids, ds_confounds, [('entities', 'entities')]),
        (grabbing_bids, ds_denoise, [('entities', 'entities')]),
        (grabbing_bids, ds_connectivity, [('entities', 'entities')]),
        (grabbing_bids, ds_carpet_plot, [('entities', 'entities')]),
        (grabbing_bids, ds_matrix_plot, [('entities', 'entities')]),
        #--- rest
        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (prep_conf, group_conf_summary, [('conf_summary', 'conf_summary'),
                                        ('pipeline_name', 'pipeline_name')]),

        (pipelineselector, ds_denoise, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_connectivity, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_confounds, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_carpet_plot, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_matrix_plot, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, denoise, [('low_pass', 'low_pass'),
                                     ('high_pass', 'high_pass')]),

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
                                                    ('edges_weight', 'edges_weight')]),
        (merge_quality_measures, pipelines_quality_measures,
            [('fc_fd_summary', 'fc_fd_summary'),
             ('edges_weight', 'edges_weight')])                                         
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

    bids_dir = '/media/finc/Elements/BIDS_pseudowords_short/BIDS_2sub/'
    output_dir = '/media/finc/Elements/BIDS_pseudowords_short/BIDS_2sub/'

    if args.bids_dir is not None:
        bids_dir = args.bids_dir
    if args.output_dir is not None:
        output_dir = args.output_dir

    wf = init_fmridenoise_wf(bids_dir)

    wf.run()
    wf.write_graph("workflow_graph.dot")
