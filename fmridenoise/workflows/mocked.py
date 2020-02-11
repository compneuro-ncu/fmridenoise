from fmridenoise.workflows.base import BaseWorkflowWithSessions, BaseWorkflow
from fmridenoise.interfaces.mocks import settings, denoising
from nipype import Node
from fmridenoise.utils import temps
from fmridenoise.interfaces.bids import BIDSValidate
from fmridenoise.pipelines import get_pipelines_paths


class DenoiseMock(BaseWorkflow):

    def _create_nodes(self, base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass):
        super()._create_nodes(base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass)
        settings.MockSettings(bids_dir=bids_dir)
        self.denoise = Node(
            denoising.Denoise(
                high_pass=high_pass,
                low_pass=low_pass,
                tr_dict=bids_validate_result.outputs.tr_dict,
                output_dir=temps.mkdtemp('denoise')),
            name="Denoiser")


class DenoiseMockWithSessions(BaseWorkflowWithSessions):
    def _create_nodes(self, base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass):
        super()._create_nodes(base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass)
        settings.MockSettings(bids_dir=bids_dir)
        self.denoise = Node(
            denoising.Denoise(
                high_pass=high_pass,
                low_pass=low_pass,
                tr_dict=bids_validate_result.outputs.tr_dict,
                output_dir=temps.mkdtemp('denoise')),
            name="Denoiser")


def init_fmridenoise_wf(bids_dir,
                        derivatives='fmriprep',
                        task=[],
                        session=[],
                        subject=[],
                        pipelines_paths=get_pipelines_paths(),
                        smoothing=True,
                        #ica_aroma=False, TODO: delete this later
                        high_pass=0.008,
                        low_pass=0.08,
                        base_dir='/tmp/fmridenoise',
                        name='fmridenoise_wf'):
    pipelines_paths = list(pipelines_paths)
    bids_validate = Node(BIDSValidate(bids_dir=bids_dir,
                               derivatives=derivatives,
                               tasks=task,
                               sessions=session,
                               subjects=subject,
                               pipelines=pipelines_paths),
                         name='BidsValidate')
    result = bids_validate.run()
    if result.outputs.sessions:
        return BaseWorkflow(name=name,
                                        base_dir=base_dir,
                                        bids_dir=bids_dir,
                                        bids_validate_result=result,
                                        pipelines_paths=pipelines_paths,
                                        high_pass=high_pass,
                                        low_pass=low_pass)
    else:
        return BaseWorkflow(name=name,
                            bids_dir=bids_dir,
                            base_dir=base_dir,
                            bids_validate_result=result,
                            pipelines_paths=pipelines_paths,
                            high_pass=high_pass,
                            low_pass=low_pass)