from nipype.interfaces.base import SimpleInterface, BaseInterfaceInputSpec
from traits.trait_types import List, Dict, Directory, File, Str

class ReportCreatorInputSpec(BaseInterfaceInputSpec):
    pipelines = List(Dict(), mandatory=True)
    tasks = List(Str(), mandaory=True)
    sessions = List(Str(), mandatory=False)    
    output_dir = Directory(exists=True)

    # excluded_subjects = List(Str(), value=()) # TODO: This mayby another input field later. 
    
    # Aggregated over pipelines
    plot_all_pipelines_edges_density = List(File(
        exists=True,
        desc="Density of edge weights (all pipelines) for all subjects"
    ))

    plot_all_pipelines_edges_density_no_high_motion = List(File(
        exist=True,
        desc="Density of edge weights (all pipelines) without high motion subjects"
    ))

    plot_all_pipelines_fc_fd_pearson_info = List(File(
        exist=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values for all subjects"
    ))

    plot_all_pipelines_fc_fd_pearson_info_no_high_motion = List(File(
        exist=True,
        desc="Barplot and violinplot showing percent of significant fc-fd correlations and distribution of Pearson's r values without high motion subjects"
    ))

    plot_all_pipelines_distance_dependence = List(File(
        exist=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs for all subject"
    ))

    plot_all_pipelines_distance_dependence_no_high_motion = List(File(
        exist=True,
        desc="Barplot showing mean Spearman's rho between fd-fc correlation and Euclidean distance between ROIs without high motion subjects"
    ))

    plot_all_pipelines_tdof_loss = List(File(
        exists=True,
        desc="..."
    ))

    # For single pipeline
    plot_pipeline_fc_fd_pearson_matrix = List(File(
        exist=True,
        desc="Matrix showing correlation between connection strength and motion for all subjects"
    ))

    plot_pipeline_fc_fd_pearson_matrix_no_high_motion = List(File(
        exist=True,
        desc="Matrix showing correlation between connection strength and motion without high motion subjects"
    ))



class ReportCreator(SimpleInterface):
    input_spec = ReportCreatorInputSpec

    def _run_interface(self, runtime):

        return runtime