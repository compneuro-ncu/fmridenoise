import argparse
from fmridenoise.interfaces.denoising import Denoise
from fmridenoise.interfaces.smoothing import Smooth
from nipype import Node, Workflow
from fmridenoise.interfaces.confounds import Confounds
from fmridenoise.pipelines import is_IcaAROMA, get_pipeline_path, load_pipeline_from_json


def run(output_dir: str, pipeline_name: str, fmri_file: str, conf_raw: str, conf_json: str):
    pipeline = load_pipeline_from_json(get_pipeline_path(pipeline_name))
    workflow = Workflow(name="test_workflow", base_dir=output_dir)
    conf_node = Node(Confounds(
        pipeline=pipeline,
        conf_raw=conf_raw,
        conf_json=conf_json,
        subject="test",
        task="test",
        session="test",
        output_dir=output_dir
    ), name="Confprep")
    denoising_node = Node(Denoise(
        pipeline=pipeline,
        task="test",
        output_dir=output_dir
    ), name="Denoise")
    if not is_IcaAROMA(pipeline):
        smoothing_node = Node(Smooth(
            fmri_prep=fmri_file
        ), name="Smooth")
        workflow.connect((smoothing_node, denoising_node, [("fmri_smoothed", "fmri_prep")]))
    else:
        denoising_node.inputs.fmri_prep_aroma = fmri_file
    workflow.connect([
        (conf_node, denoising_node, [("conf_prep", "conf_prep")])
    ])
    workflow.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--output_dir")
    parser.add_argument("-p", "--pipeline_name")
    parser.add_argument("-f", "--fmri_file")
    parser.add_argument("-r", "--conf_raw")
    parser.add_argument("-j", "--conf_json")
    args = parser.parse_args()
    run(args.output_dir, args.pipeline_name, args.fmri_file, args.conf_raw, args.conf_json)