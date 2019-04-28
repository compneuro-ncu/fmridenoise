# from ..interfaces.denoising import Denoise

from nipype.pipeline import engine as pe
from niworkflows.interfaces.bids import DerivativesDataSink as BIDSDerivatives

from fmridenoise.interfaces.loading_bids import BIDSSelect, BIDSLoad
from fmridenoise.interfaces.confounds import Confounds
from fmridenoise.interfaces.pipeline_selector import PipelineSelector

import fmridenoise
import os
import glob

# from nipype import config
# config.enable_debug_mode()


class DerivativesDataSink(BIDSDerivatives):
    out_path_base = '/home/finc/Dropbox/Projects/fitlins/BIDS/fmridenoise'


def init_fmridenoise_wf(bids_dir,
                        output_dir,
                        derivatives=True,
                        pipelines_paths = glob.glob(os.path.dirname(fmridenoise.__file__) + "/pipelines/*"),
                        #, desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                        ):

    wf = pe.Workflow(name='fmridenoise', base_dir=None)

    # 1) --- Selecting pipeline

    # Inputs: fulfilled
    #pipelineselector = pe.Node(
    #    PipelineSelector(),
    #    name="PipelineSelector")
    # pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline

    reader = pe.Node(PipelineSelector(), name="pipeline_selector") # --- this is temporary solution
    for path in glob.glob("../pipelines/*"):
        path = os.path.abspath(path)
        reader.inputs.pipeline_path = path
        pipeline = reader.run()

    # 2) --- Loading BIDS structure

    # Inputs: directory
    loading_bids = pe.Node(
        BIDSLoad(
            bids_dir=bids_dir, derivatives=derivatives
        ),
        name="BidsLoader")
    # Outputs: entities

    # 3) --- Selecting BIDS files

    # Inputs: entities
    selecting_bids = pe.MapNode(
        BIDSSelect(
            bids_dir=bids_dir,
            derivatives=derivatives
        ),
        iterfield=['entities'],
        name='BidsSelector')
    # Outputs: fmri_prep, conf_raw, entities

    # 4) --- Confounds preprocessing

    # Inputs: pipeline, conf_raw
    prep_conf = pe.MapNode(
        Confounds(pipeline=pipeline.outputs.pipeline),
        iterfield=['conf_raw'],
        name="ConfPrep")
    # Outputs: conf_prep

    # 5) --- Save derivatives

    # Inputs: conf_prep
    ds_confounds = pe.Node(DerivativesDataSink(
        suffix='prep',
    ),
        name='conf_prep',
        run_without_submitting=True)

# --- Connecting nodes

    wf.connect([
        (loading_bids, selecting_bids, [('entities', 'entities')]),
        #(pipelineselector, prep_conf), [('pipeline', 'conf_prep')],
        (selecting_bids, prep_conf, [('conf_raw', 'conf_raw')]),
        (prep_conf, ds_confounds[('conf_prep', 'in_file')]) # --- still not working with this line
    ])

    return wf

# --- TESTING

if __name__ == '__main__':
    bids_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/'
    output_dir = bids_dir
    wf = init_fmridenoise_wf(bids_dir,
                             output_dir,
                             derivatives=True)
    wf.run()
    wf.write_graph("workflow_graph.dot")