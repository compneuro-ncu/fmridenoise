from nipype.pipeline import engine as pe
from nipype import Node, IdentityInterface
from fmridenoise.interfaces.smoothing import Smooth
from fmridenoise.interfaces.bids import BIDSGrab, BIDSDataSink, BIDSValidate
from fmridenoise.interfaces.confounds import Confounds, GroupConfounds
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.connectivity import Connectivity, GroupConnectivity
from fmridenoise.interfaces.pipeline_selector import PipelineSelector
from fmridenoise.interfaces.quality_measures import QualityMeasures, PipelinesQualityMeasures
from fmridenoise.interfaces.report_creator import ReportCreator
import fmridenoise.utils.temps as temps
from fmridenoise.utils.utils import create_identity_join_node, create_flatten_identity_join_node
from fmridenoise.parcellation import get_distance_matrix_file_path
from fmridenoise.pipelines import get_pipelines_paths
import logging
import os

logger = logging.getLogger("runtime")
handler = logging.FileHandler("./runtime.log")
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


class BaseWorkflow(pe.Workflow):
    def __init__(self, name, base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass):
        super().__init__(name, base_dir)
        self._create_nodes(base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass)
        self._create_connections()

    def _create_nodes(self, base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass):

        mock_bids_dir = bids_dir
        temps.base_dir = base_dir
        # 1) --- Itersources for all further processing

        # Inputs: fulfilled
        self.pipelineselector = Node(
            PipelineSelector(),
            name="PipelineSelector")
        self.pipelineselector.iterables = ('pipeline_path', pipelines_paths)
        # Outputs: pipeline, pipeline_name, low_pass, high_pass

        # Inputs: fulfilled
        self.subjectselector = Node(
            IdentityInterface(
                fields=['subject']),
            name="SubjectSelector")
        self.subjectselector.iterables = ('subject', bids_validate_result.outputs.subjects)
        # Outputs: subject

        # Inputs: fulfilled
        # self.sessionselector = Node(
        #     IdentityInterface(
        #         fields=['session']),
        #     name="SessionSelector")
        # if bids_validate_result.outputs.session:
        #     self.sessionselector.iterables = ('session', bids_validate_result.outputs.sessions)
        # else:
        #     self.sessionselector.iterables = ('session', [traits.Undefined])

        # Inputs: fulfilled
        self.taskselector = Node(
            IdentityInterface(
                fields=['task']),
            name="TaskSelector")
        self.taskselector.iterables = ('task', bids_validate_result.outputs.tasks)
        # Outputs: task

        # 2) --- Loading BIDS files

        # Inputs: subject, session, task
        self.bidsgrabber = Node(
            BIDSGrab(
                fmri_prep_files=bids_validate_result.outputs.fmri_prep,
                fmri_prep_aroma_files=bids_validate_result.outputs.fmri_prep_aroma,
                conf_raw_files=bids_validate_result.outputs.conf_raw,
                conf_json_files=bids_validate_result.outputs.conf_json),
            name="BidsGrabber")
        # Outputs: fmri_prep, fmri_prep_aroma, conf_raw, conf_json

        # 3) --- Smoothing

        # Inputs: fmri_prep
        self.smooth_signal = Node(
            Smooth(
                output_directory=temps.mkdtemp('smoothing'),
                is_file_mandatory=False),
            name="Smoother")
        # Outputs: fmri_smoothed

        # 3) --- Confounds preprocessing

        # Inputs: pipeline, conf_raw, conf_json
        self.prep_conf = Node(
            Confounds(
                output_dir=temps.mkdtemp('prep_conf')
            ), name="ConfPrep")
        # Outputs: conf_prep, conf_summary

        # 4) --- Denoising
        # Inputs: fmri_prep, fmri_prep_aroma, conf_prep, pipeline, entity, tr_dict
        self.denoise = Node(
            Denoise(
                high_pass=high_pass,
                low_pass=low_pass,
                tr_dict=bids_validate_result.outputs.tr_dict,
                output_dir=temps.mkdtemp('denoise')),
            name="Denoiser",
            mem_gb=8)
        # Outputs: fmri_denoised

        # 5) --- Connectivity estimation

        # Inputs: fmri_denoised
        self.connectivity = Node(
            Connectivity(
                output_dir=temps.mkdtemp('connectivity')
            ),
            name='ConnCalc')
        # Outputs: conn_mat, carpet_plot

        # 6) --- Group confounds

        # Inputs: conf_summary, pipeline_name
        # FIXME BEGIN
        # This is part of temporary solution.
        # Group nodes write to bids dir insted of tmp and let files be grabbed by datasink
        os.makedirs(os.path.join(bids_dir, 'derivatives', 'fmridenoise'), exist_ok=True)
        # FIXME END
        self.group_conf_summary = pe.JoinNode(
            GroupConfounds(
                output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
            ),
            joinfield=["conf_summary_json_files"],
            joinsource=self.subjectselector,
            name="GroupConf")

        # Outputs: group_conf_summary

        # 7) --- Group connectivity

        # Inputs: corr_mat, pipeline_name

        self.group_connectivity = pe.JoinNode(
            GroupConnectivity(
                output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
            ),
            joinfield=["corr_mat"],
            joinsource=self.subjectselector,
            name="GroupConn")

        # Outputs: group_corr_mat

        # 8) --- Quality measures

        # Inputs: group_corr_mat, group_conf_summary, pipeline_name

        self.quality_measures = pe.Node(
            QualityMeasures(
                output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),
                distance_matrix=get_distance_matrix_file_path()
            ),
            name="QualityMeasures")
        # Outputs: fc_fd_summary, edges_weight, edges_weight_clean
        self.quality_measures_join = create_identity_join_node(
            name='JoinQualityMeasuresOverPipeline',
            joinsource=self.pipelineselector,
            fields=[
                'corr_matrix_plot',
                'corr_matrix_no_high_motion_plot']
        )
        # 10) --- Quality measures across pipelines

        # Inputs: fc_fd_summary, edges_weight
        self.pipelines_join = pe.JoinNode(
            IdentityInterface(fields=['pipelines']),
            name='JoinPipelines',
            joinsource=self.pipelineselector,
            joinfield=['pipelines']
        )
        self.pipelines_quality_measures = pe.JoinNode(
            PipelinesQualityMeasures(
                output_dir=os.path.join(bids_dir, 'derivatives', 'fmridenoise'),  # TODO: Replace with datasinks for needed output
            ),
            joinsource=self.pipelineselector,
            joinfield=['fc_fd_summary', 'edges_weight', 'edges_weight_clean',
                       'fc_fd_corr_values', 'fc_fd_corr_values_clean'],
            name="PipelinesQualityMeasures")
        self.pipeline_quality_measures_join = create_flatten_identity_join_node(
            name="JoinPipelinesQualityMeasuresOverTasks",
            joinsource=self.taskselector,
            fields=[
                'plot_pipelines_edges_density',
                'plot_pipelines_edges_density_no_high_motion',
                'plot_pipelines_fc_fd_pearson',
                'plot_pipelines_fc_fd_pearson_no_high_motion',
                'plot_pipelines_fc_fd_uncorr',
                'plot_pipelines_distance_dependence',
                'plot_pipelines_distance_dependence_no_high_motion',
                'plot_pipelines_tdof_loss',
                'corr_matrix_plot',
                'corr_matrix_no_high_motion_plot',
                'tasks'],
            flatten_fields=[
                'corr_matrix_plot',
                'corr_matrix_no_high_motion_plot'
            ]
        )
        # Outputs: pipelines_fc_fd_summary, pipelines_edges_weight
        # 11) --- Report from data
        report_dir = os.path.join(bids_dir, 'derivatives', 'fmridenoise', 'report')
        os.makedirs(report_dir, exist_ok=True)
        self.report_creator = pe.Node(
            ReportCreator(
                output_dir=report_dir
            ),
            name='ReportCreator')

        # 12) --- Save derivatives
        self.ds_confounds = Node(BIDSDataSink(base_directory=bids_dir),
                            name="ds_confounds")

        self.ds_denoise = Node(BIDSDataSink(base_directory=bids_dir),
                          name="ds_denoise")

        self.ds_connectivity_corr_mat = Node(BIDSDataSink(base_directory=bids_dir),
                                        name="ds_connectivity")

        self.ds_connectivity_carpet_plot = Node(BIDSDataSink(base_directory=bids_dir),
                                           name="ds_carpet_plot")

        self.ds_connectivity_matrix_plot = Node(BIDSDataSink(base_directory=bids_dir),
                                           name="ds_matrix_plot")

    def _create_connections(self):
        # --- Connecting nodes
        self.connect([
            # bidsgrabber
            (self.subjectselector, self.bidsgrabber, [('subject', 'subject')]),
            (self.taskselector, self.bidsgrabber, [('task', 'task')]),
            # smooth_signal
            (self.bidsgrabber, self.smooth_signal, [('fmri_prep', 'fmri_prep')]),
            # prep_conf
            (self.pipelineselector, self.prep_conf, [('pipeline', 'pipeline')]),
            (self.subjectselector, self.prep_conf, [('subject', 'subject')]),
            (self.taskselector, self.prep_conf, [('task', 'task')]),
            (self.bidsgrabber, self.prep_conf, [('conf_raw', 'conf_raw'),
                                      ('conf_json', 'conf_json')]),
            # denoise
            (self.smooth_signal, self.denoise, [('fmri_smoothed', 'fmri_prep')]),
            (self.prep_conf, self.denoise, [('conf_prep', 'conf_prep')]),
            (self.pipelineselector, self.denoise, [('pipeline', 'pipeline')]),
            (self.bidsgrabber, self.denoise, [('fmri_prep_aroma', 'fmri_prep_aroma')]),
            (self.taskselector, self.denoise, [('task', 'task')]),
            # group conf summary
            (self.prep_conf, self.group_conf_summary, [('conf_summary', 'conf_summary_json_files')]),
            (self.taskselector, self.group_conf_summary, [('task', 'task')]),
            (self.pipelineselector, self.group_conf_summary, [('pipeline_name', 'pipeline_name')]),
            # connectivity
            (self.denoise, self.connectivity, [('fmri_denoised', 'fmri_denoised')]),
            # group connectivity
            (self.connectivity, self.group_connectivity, [("corr_mat", "corr_mat")]),
            (self.pipelineselector, self.group_connectivity, [("pipeline_name", "pipeline_name")]),
            (self.taskselector, self.group_connectivity, [('task', 'task')]),
            # quality measures
            (self.pipelineselector, self.quality_measures, [('pipeline', 'pipeline')]),
            (self.taskselector, self.quality_measures, [('task', 'task')]),
            (self.group_connectivity, self.quality_measures, [('group_corr_mat', 'group_corr_mat')]),
            (self.group_conf_summary, self.quality_measures, [('group_conf_summary', 'group_conf_summary')]),
            # quality measure join over pipelines
            (self.quality_measures, self.quality_measures_join, 
             [('corr_matrix_plot', 'corr_matrix_plot'),
              ('corr_matrix_no_high_motion_plot', 'corr_matrix_no_high_motion_plot')]),
            # pipeline quality measures
            (self.taskselector, self.pipelines_quality_measures, [('task', 'task')]),
            (self.quality_measures, self.pipelines_quality_measures, [
                ('fc_fd_summary', 'fc_fd_summary'),
                ('edges_weight', 'edges_weight'),
                ('edges_weight_clean', 'edges_weight_clean'),
                ('fc_fd_corr_values', 'fc_fd_corr_values'),
                ('fc_fd_corr_values_clean', 'fc_fd_corr_values_clean')]),
            # pipelines_join
            (self.pipelineselector, self.pipelines_join, [('pipeline', 'pipelines')]),
            # pipeline_quality_measures_join
            (self.pipelines_quality_measures, self.pipeline_quality_measures_join, [
                ('pipelines_fc_fd_summary', 'pipelines_fc_fd_summary'),
                ('plot_pipelines_edges_density', 'plot_pipelines_edges_density'),
                ('plot_pipelines_edges_density_no_high_motion', 'plot_pipelines_edges_density_no_high_motion'),
                ('plot_pipelines_fc_fd_pearson', 'plot_pipelines_fc_fd_pearson'),
                ('plot_pipelines_fc_fd_pearson_no_high_motion', 'plot_pipelines_fc_fd_pearson_no_high_motion'),
                ('plot_pipelines_fc_fd_uncorr', 'plot_pipelines_fc_fd_uncorr'),
                ('plot_pipelines_distance_dependence', 'plot_pipelines_distance_dependence'),
                ('plot_pipelines_distance_dependence_no_high_motion', 'plot_pipelines_distance_dependence_no_high_motion'),
                ('plot_pipelines_tdof_loss', 'plot_pipelines_tdof_loss')
               ]),
            (self.taskselector, self.pipeline_quality_measures_join, [('task', 'tasks')]),
            (self.quality_measures_join, self.pipeline_quality_measures_join,
             [('corr_matrix_plot', 'corr_matrix_plot'),
              ('corr_matrix_no_high_motion_plot', 'corr_matrix_no_high_motion_plot')]),
            # report creator
            (self.pipelines_join, self.report_creator, [('pipelines', 'pipelines')]),
            (self.pipeline_quality_measures_join, self.report_creator, [
                ('tasks', 'tasks'),
                ('plot_pipelines_edges_density', 'plots_all_pipelines_edges_density'),
                ('plot_pipelines_edges_density_no_high_motion', 'plots_all_pipelines_edges_density_no_high_motion'),
                ('plot_pipelines_fc_fd_pearson', 'plots_all_pipelines_fc_fd_pearson_info'),
                ('plot_pipelines_fc_fd_pearson_no_high_motion', 'plots_all_pipelines_fc_fd_pearson_info_no_high_motion'),
                ('plot_pipelines_distance_dependence', 'plots_all_pipelines_distance_dependence'),
                ('plot_pipelines_distance_dependence_no_high_motion', 'plots_all_pipelines_distance_dependence_no_high_motion'),
                ('plot_pipelines_tdof_loss', 'plots_all_pipelines_tdof_loss'),
                ('corr_matrix_plot', 'plots_pipeline_fc_fd_pearson_matrix'),
                ('corr_matrix_no_high_motion_plot', 'plots_pipeline_fc_fd_pearson_matrix_no_high_motion'),
            ]),
            # all datasinks
            ## ds_denoise
            (self.subjectselector, self.ds_denoise, [("subject", "subject")]),
            (self.denoise, self.ds_denoise, [("fmri_denoised", "in_file")]),
            ## ds_connectivity
            (self.subjectselector, self.ds_connectivity_corr_mat, [("subject", "subject")]),
            (self.connectivity, self.ds_connectivity_corr_mat, [("corr_mat", "in_file")]),
            (self.subjectselector, self.ds_connectivity_matrix_plot, [("subject", "subject")]),
            (self.connectivity, self.ds_connectivity_matrix_plot, [("matrix_plot", "in_file")]),
            (self.subjectselector, self.ds_connectivity_carpet_plot, [("subject", "subject")]),
            (self.connectivity, self.ds_connectivity_carpet_plot, [("carpet_plot", "in_file")]),
            ## ds_confounds
            (self.subjectselector, self.ds_confounds, [("subject", "subject")]),
            (self.prep_conf, self.ds_confounds, [("conf_prep", "in_file")]),
        ])


class BaseWorkflowWithSessions(BaseWorkflow):

    def _create_nodes(self, base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass):
        super()._create_nodes(base_dir, bids_dir, bids_validate_result, pipelines_paths, high_pass, low_pass)
        self.sessionselector = Node(
            IdentityInterface(
                fields=['session']),
            name="SessionSelector")
        self.sessionselector.iterables = ('session', bids_validate_result.outputs.sessions)
        # Outputs: session

    def _create_connections(self):
        super()._create_connections()
        self.connect([
            (self.sessionselector, self.bidsgrabber, [('session', 'session')]),
            (self.sessionselector, self.prep_conf, [('session', 'session')]),
            (self.sessionselector, self.group_conf_summary, [('session', 'session')]),
            (self.sessionselector, self.group_connectivity, [('session', 'session')]),
            (self.sessionselector, self.quality_measures, [('session', 'session')]),
            (self.sessionselector, self.ds_denoise, [("session", "session")]),
            (self.sessionselector, self.ds_connectivity_corr_mat, [("session", "session")]),
            (self.sessionselector, self.ds_connectivity_matrix_plot, [("session", "session")]),
            (self.sessionselector, self.ds_connectivity_carpet_plot, [("session", "session")]),
            (self.sessionselector, self.ds_confounds, [("session", "session")]),
        ])


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
        return BaseWorkflowWithSessions(name=name,
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
