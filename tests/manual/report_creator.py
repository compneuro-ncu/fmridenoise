import argparse
from nipype import Workflow, Node
from nipype.interfaces.base import Undefined
from fmridenoise.pipelines import get_pipeline_path
from fmridenoise.pipelines import load_pipeline_from_json
from fmridenoise.interfaces.report_creator import ReportCreator
from nipype.interfaces.utility import IdentityInterface
import typing as t
from os import makedirs
from os.path import join


def run(output_dir: str,
        pipelines: t.List[str],
        tasks: t.List[str],
        sessions: t.Union[t.List[str], t.Any],
        plot_pipelines_edges_density: t.List[str],
        plot_pipelines_edges_density_no_high_motion: t.List[str],
        plot_pipelines_fc_fd_pearson: t.List[str],
        plot_pipelines_fc_fd_uncorr: t.List[str],
        plot_pipelines_distance_dependence: t.List[str]
        ):
    if sessions is None:
        sessions = Undefined
    pipelines = [load_pipeline_from_json(get_pipeline_path(pipeline)) for pipeline in pipelines]
    workflow = Workflow(name="test_workflow", base_dir=output_dir)
    identity_node = Node(
        IdentityInterface(fields=['output_dir',
                                  'pipelines',
                                  'tasks',
                                  'sessions',
                                  'plot_pipelines_edges_density',
                                  'plot_pipelines_edges_density_no_high_motion',
                                  'plot_pipelines_fc_fd_pearson',
                                  'plot_pipelines_fc_fd_uncorr',
                                  'plot_pipelines_distance_dependence']),
        name='SomeInputSource')
    makedirs(join(output_dir, "report"), exist_ok=True)
    identity_node.inputs.output_dir = output_dir
    identity_node.inputs.pipelines = pipelines
    identity_node.inputs.tasks = tasks
    if sessions != Undefined:
        identity_node.inputs.sessions = sessions,
    identity_node.inputs.plot_pipelines_edges_density = plot_pipelines_edges_density
    identity_node.inputs.plot_pipelines_edges_density_no_high_motion = plot_pipelines_edges_density_no_high_motion
    identity_node.inputs.plot_pipelines_fc_fd_pearson = plot_pipelines_fc_fd_pearson
    identity_node.inputs.plot_pipelines_fc_fd_uncorr = plot_pipelines_fc_fd_uncorr
    identity_node.inputs.plot_pipelines_distance_dependence = plot_pipelines_distance_dependence
    report_node = Node(ReportCreator(), name='ReportCreatorNode')
    workflow.connect([(identity_node, report_node, [
        ('output_dir', 'output_dir'),
        ('pipelines', 'pipelines'),
        ('tasks', 'tasks'),
        ('sessions', 'sessions'),
        ('plot_pipelines_edges_density', 'plot_pipelines_edges_density'),
        ('plot_pipelines_edges_density_no_high_motion', 'plot_pipelines_edges_density_no_high_motion'),
        ('plot_pipelines_fc_fd_pearson', 'plot_pipelines_fc_fd_pearson'),
        ('plot_pipelines_fc_fd_uncorr', 'plot_pipelines_fc_fd_uncorr'),
        ('plot_pipelines_distance_dependence', 'plot_pipelines_distance_dependence')
    ])])
    workflow.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output_dir', required=True)
    parser.add_argument('-p', '--pipelines', nargs='+', required=True)
    parser.add_argument('-t', '--tasks', nargs='+', required=True)
    parser.add_argument('-s', '--sessions', nargs='+', required=False)
    parser.add_argument('--edges_density', nargs='+', required=True)
    parser.add_argument('--edges_density_no_high_motion', nargs='+', required=True)
    parser.add_argument('--fc_fd_pearson', nargs='+', required=True)
    parser.add_argument('--fc_fd_uncorr', nargs='+', required=True)
    parser.add_argument('--distance_dependence', nargs='+', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.pipelines, args.tasks, args.sessions, args.edges_density,
        args.edges_density_no_high_motion, args.fc_fd_pearson, args.fc_fd_uncorr, args.distance_dependence)
