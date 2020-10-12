from nipype.interfaces.base import SimpleInterface, BaseInterfaceInputSpec
from traits.trait_types import List, Dict, Directory, File, Str
from fmridenoise.utils.report import create_report


class ReportCreatorInputSpec(BaseInterfaceInputSpec):
    pipelines = List(Dict(), mandatory=True)
    tasks = List(Str(), mandaory=True)
    output_dir = Directory(exists=True)

    # excluded_subjects = List(Str(), value=())
    # sessions = List(Str(), mandatory=False)
    plot_pipelines_edges_density = List(File(
        exists=True,
        desc="Density of edge weights (all subjects)"
    ))

    plot_pipelines_edges_density_no_high_motion = List(File(
        exist=True,
        desc="Density of edge weights (no high motion)"
    ))

    plot_pipelines_fc_fd_pearson = List(File(
        exist=True
    ))

    plot_pipelines_fc_fd_uncorr = List(File(
        exist=True
    ))

    plot_pipelines_distance_dependence = List(File(
        exist=True
    ))


class ReportCreator(SimpleInterface):
    input_spec = ReportCreatorInputSpec

    def _run_interface(self, runtime):
        # create_report(self.inputs.group_data_dir,
        #               self.inputs.pipelines,
        #               self.inputs.excluded_subjects)
        with open(f"{self.inputs.output_dir}/log.log", 'a') as f:
            f.writelines('Called\n' + str(self.inputs) + '\n' + str(self.inputs.pipelines))
        return runtime