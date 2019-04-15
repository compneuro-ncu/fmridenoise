from nipype.pipeline import engine as pe
from ..interfaces.loading_bids import (
    PipelineSpecLoader, LoadPipeline, BIDSSelect, BIDSDataSink)
from ..interfaces.denoising import Denoising

def init_fmridenoise_wf(bids_dir, derivatives, out_dir, pipelines_dir, desc=None,
                        ignore=None, force_index=None,
                        model=None, participants=None,
                        base_dir=None, name='fmridenoise_wf'):
    wf = pe.Workflow(name=name, base_dir=base_dir)

    # Find the appropriate pipeline file(s)
    specs = PipelineSpecLoader(pipelines_dir=pipelines_dir) #--> create this interface
    #if model is not None:
    #    specs.inputs.model = model

    pipeline_dict = specs.run().outputs.pipeline_spec #--> create this interface

    if not pipeline_dict:
        raise RuntimeError("Unable to find pipeline specification file")
    #if isinstance(model_dict, list):
    #    raise RuntimeError("Currently unable to run multiple models in parallel - "
    #                       "please specify model")


    loader = pe.Node(
            LoadBIDSModel(bids_dir=bids_dir,
                          derivatives=derivatives,
                          pipeline=pipeline_dict),
            name='loader')


    # Select preprocessed BOLD series to analyze
    getter = pe.Node(
        BIDSSelect(
            bids_dir=bids_dir, derivatives=derivatives,
            selectors={
                'suffix': 'bold',
                'desc': desc),
            name='getter')

    denoising = pe.MapNode(
        Denoising(),
        iterfield=['session_info', 'bold_file', 'confounds'],
        name='denoising')


    # General connections
    wf.connect([
        (loader,
        getter,
        denoising)
