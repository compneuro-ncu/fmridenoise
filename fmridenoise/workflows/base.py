from ..interfaces.denoising import Denoise
from..interfaces.pipeline_selector import PipelineSelector
import fmridenoise
import os
import glob
from nipype import Node, Workflow
from ..interfaces.bids import BIDSSelect


def init_fmridenoise_wf(bids_dir, derivatives, entities,
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

    loading_bids = Node(
        BIDSSelect(
            bids_dir=bids_dir,
            derivatives=True,
            entities=entities),
        name='loading_bids')
    # Outputs: bold_files, confounds_files, entities

    denoising = Node(
        Denoise(),
        name='denoising')

    # General connections
    wf.connect([loading_bids, denoising, [('bold', 'bold_files'),
                                          ('confound', 'confound_files')]])

#prepconfounds = Node()

