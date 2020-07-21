import argparse
from fmridenoise.interfaces import PipelinesQualityMeasures
from nipype import Node, Workflow
from nipype.interfaces.utility import IdentityInterface
from fmridenoise.parcellation import get_distance_matrix_file_path
from numpy import array
edges_weight = [
    {'24HMP8PhysSpikeReg': array([0.70710678, 0.48339738, 0.70710678, 0.2699669, 0.64224707, 0.70710678])},
    {'Null': array([0.70710678, 0.7526871, 0.70710678, 0.6626035, 0.81092814, 0.70710678])}
]
edges_weight_clean = [
    {'24HMP8PhysSpikeReg': array([0.70710678, 0.48339738, 0.70710678, 0.2699669, 0.64224707, 0.70710678])},
    {'Null': array([0.70710678, 0.7526871, 0.70710678, 0.6626035, 0.81092814, 0.70710678])}]
fc_fd_summary = [
    [
        {'all': True,
        'distance_dependence': -0.04001843958201733,
        'n_excluded': 0,
        'n_subjects': 3,
        'pearson_fc_fd': 0.2837382791803038,
        'perc_fc_fd_uncorr': 4.248756218905473,
        'pipeline': '24HMP8PhysSpikeReg',
        'tdof_loss': 38.333333333333336},
        {'all': False,
        'distance_dependence': -0.04001843958201733,
        'n_excluded': 0,
        'n_subjects': 3,
        'pearson_fc_fd': 0.2837382791803038,
        'perc_fc_fd_uncorr': 4.248756218905473,
        'pipeline': '24HMP8PhysSpikeReg',
        'tdof_loss': 38.333333333333336}
    ],
    [
        {'all': True,
        'distance_dependence': -0.06304964769937552,
        'n_excluded': 0,
        'n_subjects': 3,
        'pearson_fc_fd': 0.4903626077607741,
        'perc_fc_fd_uncorr': 5.1393034825870645,
        'pipeline': 'Null',
        'tdof_loss': 0.0},
        {'all': False,
        'distance_dependence': -0.06304964769937552,
        'n_excluded': 0,
        'n_subjects': 3,
        'pearson_fc_fd': 0.4903626077607741,
        'perc_fc_fd_uncorr': 5.1393034825870645,
        'pipeline': 'Null',
        'tdof_loss': 0.0}
    ]
]
task = 'prlrew'


def run(output_dir: str):
    workflow = Workflow(name="test_workflow", base_dir=output_dir)
    identity_node = Node(
        IdentityInterface(fields=["edges_weight", "edges_weight_clean", "fc_fc_summary", "task"]),
        name="SomeInputSource")
    identity_node.inputs.edges_weight = edges_weight
    identity_node.inputs.edges_weight_clean = edges_weight_clean
    identity_node.inputs.fc_fd_summary = fc_fd_summary
    identity_node.inputs.task = task
    quality_node = Node(PipelinesQualityMeasures(
        output_dir=output_dir),
        name="PipelineQualitMeasures")
    workflow.connect([(identity_node, quality_node, [
        ("edges_weight_clean", "edges_weight_clean"),
        ("edges_weight", "edges_weight"),
        ("fc_fd_summary", "fc_fd_summary"),
        ("task", "task")
    ])])
    workflow.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--output_dir", help="Output data/working directory", required=True)
    args = parser.parse_args()
    run(args.output_dir)