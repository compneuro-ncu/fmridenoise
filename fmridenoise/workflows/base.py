from nipype.pipeline import engine as pe

from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink
from fmridenoise.interfaces.confounds import Confounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector

import fmridenoise
import os
import glob

def init_fmridenoise_wf(bids_dir,
                        output_dir,
                        derivatives='fmriprep',
                        task=[],
                        pipelines_paths=glob.glob(os.path.dirname(fmridenoise.__file__) + "/pipelines/*"),
                        # desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                        ):

    workflow = pe.Workflow(name='fmridenoise', base_dir=None)

    # 1) --- Selecting pipeline

    # Inputs: fulfilled
    pipelineselector = pe.Node(
       PipelineSelector(),
       name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline

    # 2) --- Loading BIDS structure

    # Inputs: directory, task, derivatives
    grabbing_bids = pe.Node(
        BIDSGrab(
            bids_dir=bids_dir,
            derivatives=derivatives,
            task=task
        ),
        name="BidsGrabber")
    # Outputs: fmri_prep, conf_raw, entities

    # 3) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw
    prep_conf = pe.MapNode(
        Confounds(
            output_dir=output_dir
        ),
        iterfield=['conf_raw'],
        name="ConfPrep")
    # Outputs: conf_prep, low_pass, high_pass

    # 4) --- Denoising

    # Inputs: conf_prep, low_pass, high_pass
    denoise = pe.MapNode(
        Denoise(
            output_dir=output_dir,
        ),
        iterfield=['fmri_prep', 'conf_prep'], #, 'low_pass', 'high_pass'],
        name="Denoiser")
    # Outputs: fmri_denoised

    # 5) --- Connectivity estimation

    # Inputs: fmri_denoised
    parcellation_path = os.path.abspath(os.path.join(fmridenoise.__path__[0], "parcellation"))
    parcellation_path = glob.glob(parcellation_path + "/*")[0]

    connectivity = pe.MapNode(
        Connectivity(output_dir=output_dir, parcellation=parcellation_path),
        iterfield=['fmri_denoised'],
        name='ConnCalc')
    # Outputs: conn_mat, carpet_plot

    # 6) --- Save derivatives
    # TODO: Fill missing in/out
    ds_confounds = pe.MapNode(BIDSDataSink(base_directory=output_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_confounds")
    ds_denoise = pe.MapNode(BIDSDataSink(base_directory=output_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_denoise")
    ds_connectivity = pe.MapNode(BIDSDataSink(base_directory=output_dir),
                    iterfield=['in_file', 'entities'],
                    name="ds_connectivity")

    ds_carpet_plot = pe.MapNode(BIDSDataSink(base_directory=output_dir),
                                 iterfield=['in_file', 'entities'],
                                 name="ds_carpet_plot")

    ds_matrix_plot = pe.MapNode(BIDSDataSink(base_directory=output_dir),
                                 iterfield=['in_file', 'entities'],
                                 name="ds_matrix_plot")


# --- Connecting nodes

    workflow.connect([
        (grabbing_bids, denoise, [('fmri_prep', 'fmri_prep')]),
        (grabbing_bids, prep_conf, [('conf_raw', 'conf_raw')]),
        (grabbing_bids, ds_confounds, [('entities', 'entities')]),
        (grabbing_bids, ds_denoise, [('entities', 'entities')]),
        (grabbing_bids, ds_connectivity, [('entities', 'entities')]),
        (grabbing_bids, ds_carpet_plot, [('entities', 'entities')]),
        (grabbing_bids, ds_matrix_plot, [('entities', 'entities')]),
        #--- rest
        (pipelineselector, prep_conf, [('pipeline', 'pipeline')]),
        (pipelineselector, ds_denoise, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_connectivity, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_confounds, [('pipeline_name','pipeline_name')]),
        (pipelineselector, ds_carpet_plot, [('pipeline_name', 'pipeline_name')]),
        (pipelineselector, ds_matrix_plot, [('pipeline_name', 'pipeline_name')]),
        (prep_conf, denoise, [('conf_prep', 'conf_prep')]),
        (denoise, connectivity, [('fmri_denoised', 'fmri_denoised')]),
        (prep_conf, ds_confounds, [('conf_prep', 'in_file')]),
        (denoise, ds_denoise, [('fmri_denoised', 'in_file')]),
        (connectivity, ds_connectivity, [('corr_mat', 'in_file')]),
        (connectivity, ds_carpet_plot, [('carpet_plot', 'in_file')]),
        (connectivity, ds_matrix_plot, [('matrix_plot', 'in_file')]),
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

    bids_dir = '/home/kmb/Desktop/Neuroscience/Projects/NBRAINGROUP_fmridenoise/test_data/BIDS_2sub'
    output_dir = '/home/kmb/Desktop/Neuroscience/Projects/NBRAINGROUP_fmridenoise/test_data/BIDS_2sub'

    if args.bids_dir is not None:
        bids_dir = args.bids_dir
    if args.output_dir is not None:
        output_dir = args.output_dir

    wf = init_fmridenoise_wf(bids_dir,
                             output_dir)

    wf.run()
    wf.write_graph("workflow_graph.dot")