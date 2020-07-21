# TODO: Make try replacing both interfaces with identity interface on JoinNode
from nipype.interfaces.base import SimpleInterface, BaseInterfaceInputSpec, TraitedSpec, traits


class JoinPipelinesInputSpec(BaseInterfaceInputSpec):
    pipelines = traits.List(traits.Dict())


class JoinPipelinesOutputSpec(TraitedSpec):
    pipelines = traits.List(traits.Dict())


class JoinPipelines(SimpleInterface):
    input_spec = JoinPipelinesInputSpec
    output_spec = JoinPipelinesOutputSpec

    def _run_interface(self, runtime):
        self._results['pipelines'] = self.inputs.pipelines
        return runtime


class JoinPipelineQualityMeasuresInputSPec(BaseInterfaceInputSpec):
    tasks = traits.List(traits.Str(), mandaory=True)

    plot_pipelines_edges_density = traits.List(traits.File(
        exists=True,
        desc="Density of edge weights (all subjects)"
    ))

    plot_pipelines_edges_density_no_high_motion = traits.List(traits.File(
        exist=True,
        desc="Density of edge weights (no high motion)"
    ))

    plot_pipelines_fc_fd_pearson = traits.List(traits.File(
        exist=True
    ))

    plot_pipelines_fc_fd_uncorr = traits.List(traits.File(
        exist=True
    ))

    plot_pipelines_distance_dependence = traits.List(traits.File(
        exist=True
    ))


class JoinPipelineQualityMeasuresOutputSpec(TraitedSpec):
    tasks = traits.List(traits.Str(), mandaory=True)

    plot_pipelines_edges_density = traits.List(traits.File(
        exists=True,
        desc="Density of edge weights (all subjects)"
    ))

    plot_pipelines_edges_density_no_high_motion = traits.List(traits.File(
        exist=True,
        desc="Density of edge weights (no high motion)"
    ))

    plot_pipelines_fc_fd_pearson = traits.List(traits.File(
        exist=True
    ))

    plot_pipelines_fc_fd_uncorr = traits.List(traits.File(
        exist=True
    ))

    plot_pipelines_distance_dependence = traits.List(traits.File(
        exist=True
    ))


class JoinPipelineQualityMeasures(SimpleInterface):
    input_spec = JoinPipelineQualityMeasuresInputSPec
    output_spec = JoinPipelineQualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        self._results['tasks'] = self.inputs.tasks
        self._results['plot_pipelines_edges_density'] = self.inputs.plot_pipelines_edges_density
        self._results['plot_pipelines_edges_density_no_high_motion'] = self.inputs.plot_pipelines_edges_density_no_high_motion
        self._results['plot_pipelines_fc_fd_pearson'] = self.inputs.plot_pipelines_fc_fd_pearson
        self._results['plot_pipelines_fc_fd_uncorr'] = self.inputs.plot_pipelines_fc_fd_uncorr
        self._results['plot_pipelines_distance_dependence'] = self.inputs.plot_pipelines_distance_dependence
        return runtime