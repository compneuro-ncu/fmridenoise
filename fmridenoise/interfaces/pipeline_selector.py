from nipype.interfaces.base import SimpleInterface, BaseInterfaceInputSpec, TraitedSpec
from traits.trait_types import List, Dict, File
from fmridenoise.utils.utils import load_pipeline_from_json
from fmridenoise.utils.json_validator import is_valid
import os


class PipelineSelectorInputSpecification(BaseInterfaceInputSpec):
    pipeline_path = File(exists=True)


class PipelineSelectorOutPutSpecification(TraitedSpec):
    pipeline = Dict(items=True)


class PipelineSelector(SimpleInterface):
    input_spec = PipelineSelectorInputSpecification
    output_spec = PipelineSelectorOutPutSpecification

    def _run_interface(self, runtime):
        js = load_pipeline_from_json(self.inputs.pipeline_path)
        if not is_valid(js):
            raise ValueError("""
            Json file {} is not a valid pipeline, 
            check schema at fmridenoise.utils.json_validator.py
            """.format(os.path.basename(self.inputs.pipeline_path)))
        self._results['pipeline'] = js
        return runtime

# rudimentary test # TODO: Move to this to proper unittests
if __name__ == '__main__':
    from nipype import Node
    import glob
    reader = Node(PipelineSelector(), name="pipeline_selector")
    for path in glob.glob("../pipelines/*"):
        path = os.path.abspath(path)
        print(path)
        reader.inputs.pipeline_path = path
        results = reader.run()

    print(results.outputs)
