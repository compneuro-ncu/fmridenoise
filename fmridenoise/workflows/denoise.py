from nipype import Workflow, Node
from bids.layout import BIDSLayout
from fmridenoise.interfaces import Denoise, Confounds
from fmridenoise.utils import temps
from fmridenoise.pipelines import is_IcaAROMA, load_pipeline_from_json


def create_denoise_workflow(name: str, base_dir: str, bids_dir: str, bids_layout: BIDSLayout, pipeline_path: str,
                            low_pass: float, high_pass: float):
    pipeline = load_pipeline_from_json(pipeline_path)
    workflow = Workflow(name, base_dir)
    is_IcaAROMA(pipeline)
    denoise_node = Node(
        Denoise(
            low_pass=low_pass,
            high_pass=high_pass,
            output_dir=temps.mkdtemp('denoise')),
        name='Denoiser',
        mem_gb=8)
    conf_prep = Node(
        Confounds(
            pipeline=pipeline,
            output_dir=temps.mkdtemp('prep_conf')
        ),
        name='ConfPrep'
    )
    workflow.connect([
        (conf_prep, denoise_node, [('conf_prep', 'conf_prep')])
    ])
