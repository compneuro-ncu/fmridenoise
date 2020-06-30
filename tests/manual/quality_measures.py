import argparse
from fmridenoise.interfaces import QualityMeasures
from nipype import Node, Workflow
from nipype.interfaces.utility import IdentityInterface
from fmridenoise.parcellation import get_distance_matrix_file_path


def run(output_dir: str, pipeline_name: str, group_corr_mat: str, group_conf_summary: str):
    workflow = Workflow(name="test_workflow", base_dir=output_dir)
    identity_node = Node(
        IdentityInterface(fields=["pipeline_name", "group_corr_mat", "distance_matrix", "group_conf_summary"]),
        name="SomeInputSource")
    identity_node.inputs.pipeline_name = pipeline_name
    identity_node.inputs.group_corr_matt = group_corr_mat
    identity_node.inputs.distance_matrix = get_distance_matrix_file_path()
    identity_node.inputs.group_conf_summary = group_conf_summary
    quality_node = Node(QualityMeasures(
        output_dir=output_dir),
        name="Confprep")
    workflow.connect([(identity_node, quality_node, [
        ("pipeline_name", "pipeline_name"),
        ("group_corr_mat", "group_corr_mat"),
        ("distance_matrix", "distance_matrix"),
        ("group_conf_summary", "group_conf_summary")
    ])])
    workflow.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--output_dir", required=True)
    parser.add_argument("-p", "--pipeline_name", required=True)
    parser.add_argument("-s", "--group_conf_summary", required=True)
    parser.add_argument("-c", "--group_corr_mat", required=True)
    args = parser.parse_args()
    run(args.output_dir, args.pipeline_name, args.group_corr_mat, args.group_conf_summary)