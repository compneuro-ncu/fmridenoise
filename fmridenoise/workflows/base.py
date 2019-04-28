# from ..interfaces.denoising import Denoise

from nipype.pipeline import engine as pe
from niworkflows.interfaces.bids import DerivativesDataSink as BIDSDerivatives

from fmridenoise.interfaces.loading_bids import BIDSSelect, BIDSLoad
from fmridenoise.interfaces.confounds import Confounds
from fmridenoise.interfaces.pipeline_selector import PipelineSelector

import fmridenoise
import os
import glob

# from nipype import Node, Workflow, Function, MapNode
# from nipype import config

# config.enable_debug_mode()


class DerivativesDataSink(BIDSDerivatives):
    out_path_base = '/home/finc/Dropbox/Projects/fitlins/BIDS/fmridenoise'


def init_fmridenoise_wf(bids_dir, derivatives=True,
                        # out_dir,
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

    reader = pe.Node(PipelineSelector(), name="pipeline_selector")
    for path in glob.glob("../pipelines/*"):
        path = os.path.abspath(path)
        print(path)
        reader.inputs.pipeline_path = path
        pipeline = reader.run()

    # pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: pipeline

    # 2) --- Loading BIDS structure

    # Inputs: directory
    loading_bids = pe.Node(
        BIDSLoad(
            bids_dir=bids_dir, derivatives=derivatives
        ),
        name="BidsLoader")
    # loading_bids.inputs.bids_dir = bids_dir
    # loading_bids.inputs.derivatives = derivatives
    # Outputs: entities

    # 3) --- Selecting BIDS files

    # Inputs: entities
    selecting_bids = pe.Node(
        BIDSSelect(
            bids_dir=bids_dir, derivatives=derivatives
        ),
        name='BidsSelector')
    # selecting_bids.inputs.bids_dir = bids_dir
    # selecting_bids.inputs.derivatives = derivatives
    # selecting_bids.inputs.selectors = None
    # Outputs: fmri_prep, conf_raw, entities

    # 4) Confounds preprocessing

    prep_conf = pe.MapNode(
        Confounds(pipeline=pipeline.outputs.pipeline),
        iterfield=['conf_raw'],
        name="ConfPrep")


    # denoising = Node(
    #     Denoise(),
    #     name='denoising')


    # General connections

    wf.connect([
        (loading_bids, selecting_bids, [('entities', 'entities')]),
        #(pipelineselector, prep_conf), [('pipeline', 'conf_prep')],
        (selecting_bids, prep_conf, [('conf_raw', 'conf_raw')])
    ])

    return wf



if __name__ == '__main__':
    bids_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/'
    wf = init_fmridenoise_wf(bids_dir, derivatives=True)
    wf.run()
    wf.write_graph("workflow_graph.dot")