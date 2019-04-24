from nipype.pipeline import engine as pe
from ..interfaces.loading_bids import (
    PipelineSpecLoader, LoadPipeline, BIDSSelect, BIDSDataSink)
from ..interfaces.denoising import Denoising
from ..interfaces.loading_bids import BIDSSelect

def init_fmridenoise_wf(bids_dir, derivatives, entities,
                        #out_dir, 
                        #pipelines_dir, desc=None,
                        #ignore=None, force_index=None,
                        #model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'
                       ):
    
    wf = pe.Workflow(name='fmridenoise', base_dir=None)

    loading_bids = pe.Node(
                BIDSSelect(
                    bids_dir=bids_dir, 
                    derivatives=True, 
                    entities = entities),
                name='loading_bids')
                # Outputs: bold_files, confounds_files, entities 

    denoising = pe.Node(
            Denoise(),
            name='denoising')


        # General connections
    wf.connect([loading_bids, denoising, [('bold','bold_files'), 
                                          ('confound', 'confound_files')]])