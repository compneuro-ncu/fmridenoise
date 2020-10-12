from nipype.interfaces.base import TraitedSpec, traits, BaseInterfaceInputSpec, SimpleInterface
from itertools import chain


class JoinPipelineQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List(traits.List(
        exists=True,
        desc='QC-FC quality measures'))

    edges_weight = traits.List(traits.Dict(
        exists=True,
        desc='Weights of individual edges'))

    edges_weight_clean = traits.List(traits.Dict(
        exists=True,
        desc='Weights of individual edges after '
             'removing subjects with high motion'))

    exclude_list = traits.List(traits.List(
        exists=True,
        desc="List of subjects to exclude"))


class JoinPipelineQualityMeasuresOutputSpec(TraitedSpec):
    fc_fd_summary = traits.List(
        exists=True,
        desc='QC-FC quality measures')

    edges_weight = traits.Dict(
        exists=True,
        desc='Weights of individual edges')

    edges_weight_clean = traits.Dict(
        exists=True,
        desc='Weights of individual edges after '
             'removing subjects with high motion')

    exclude_list = traits.List(
        exists=True,
        desc="List of subjects to exclude")


class JoinPipelineQualityMeasures(SimpleInterface):

    input_spec = JoinPipelineQualityMeasuresInputSpec
    output_spec = JoinPipelineQualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        self._results['fc_fd_summary'] = list(chain(self.inputs.fc_fd_summary))
        self._results['edges_weight'] = list(chain(self.inputs.edges_weight))
        self._results['edges_weight_clean'] = list(chain(self.inputs.edges_weight_clean))
        self._results['exclude_list'] = list(chain(self.inputs.exclude_list))
        return runtime