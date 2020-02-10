from fmridenoise.interfaces.denoising import Denoise, DenoiseInputSpec
from traits.trait_types import Dict, Str, Float, Directory, File
from .mock_tools import *
from os.path import join
from glob import  glob


class DenoiseMockInputSpec(DenoiseInputSpec):

    conf_prep = File(
        exists=True,
        desc="Confound file",
        mandatory=False
    )

    tr_dict = Dict(
        desc="dictionary of tr for all tasks",
        mandatory=False
    )

    high_pass = Float(
        desc="High-pass filter",
        mandatory=False
    )

    low_pass = Float(
        desc="Low-pass filter",
        mandatory=False
    )


class Denoise(Denoise):

    input_spec = DenoiseMockInputSpec

    def _run_interface(self, runtime):
        assert self.inputs.fmri_prep is not None or self.inputs.fmri_prep_aroma is not None, \
            "Both fmri_prep and fmri_prep_aroma is missing"
        pipeline_aroma = self.inputs.pipeline['aroma']
        if pipeline_aroma:
            if self.inputs.fmri_prep_aroma is None:
                raise ValueError("Fmriprep aroma file is missing")
            path = self.inputs.fmri_prep_aroma
        else:
            if self.inputs.fmri_prep is None:
                raise ValueError("Fmriprep file is missing")
            path = self.inputs.fmri_prep

        entities = explode_into_entities(path)
        files = self.queery_for_denoised_file_path(entities, self.inputs.pipeline["name"])
        assert len(files) == 1, f"Ambiguous ({len(files)}) number of files was returned"
        self._results['fmri_denoised'] = files[0]
        return runtime

    @staticmethod
    def queery_for_denoised_file_path(entities, pipeline_name):
        entities.overwrite("derivatives", "fmridenoise")
        entities["pipeline"] = pipeline_name
        path = join(entities["dataset_directory"], "derivatives", "fmridenoise")
        if entities["session"]:
            path = join(path, f"ses-{entities['session']}")
        if entities["subject"]:
            path = join(path, f"sub-{entities['session']}")
        all_files_at_path = glob(join(path, "**/*"), recursive=True)
        check_file = lambda file_path: all(entity_value in file_path for entity_value in entities.values())
        result = list(filter(check_file, all_files_at_path))
        return result


if __name__ == "__main__":
    entities = explode_into_entities(r"/mnt/Data/new_dataset/derivatives/fmriprep/sub-m02/func/sub-m03_task-prlrew_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
    print(entities)
    print(Denoise.build_denoised_file_path(entities, "Null"))