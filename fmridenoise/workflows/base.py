from ..interfaces.denoising import Denoise
from..interfaces.pipeline_selector import PipelineSelector
import fmridenoise
import os
import glob
from nipype import Node, Workflow
from ..interfaces.loading_bids import BIDSSelect, BIDSLoad


def init_fmridenoise_wf(bids_dir, derivatives,
                        # out_dir,
                        pipelines_paths = glob.glob(os.path.dirname(fmridenoise.__file__) + "/pipelines/*"),
                        #, desc=None,
                        # ignore=None, force_index=None,
                        # model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                        ):
    wf = Workflow(name='fmridenoise', base_dir=None)

    # Inputs: fulfilled
    pipelineselector = Node(PipelineSelector(), name="PipelineSelector")
    pipelineselector.iterables = ('pipeline_path', pipelines_paths)
    # Outputs: dictionary with pipeline
    # Inputs: directory
    loading_bids = Node(BIDSLoad(), name="BidsLoader")
    loading_bids.inputs.bids_dir = bids_dir
    loading_bids.inputs.derivatives = True
    # Outputs: entities
    selecting_bids = Node(
        BIDSSelect(),
        name='BidsSelector')
    selecting_bids.inputs.bids_dir = bids_dir
    selecting_bids.inputs.derivatives = True
    selecting_bids.inputs.selectors = None
    # Outputs: bold_files, confounds_files, entities

    denoising = Node(
        Denoise(),
        name='denoising')

    # General connections
    wf.connect([loading_bids, selecting_bids, ('entities', 'entities')])

#prepconfounds = Node()

