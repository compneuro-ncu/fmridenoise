from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec,
    ImageFile, SimpleInterface, Directory)
from nibabel import load, save
from nilearn.image import smooth_img
from fmridenoise.utils.entities import explode_into_entities
from os.path import join, exists
from traits.trait_types import Bool


class SmoothInputSpec(BaseInterfaceInputSpec):
    fmri_prep = ImageFile(
        desc='Preprocessed fMRI file'
    )
    is_file_mandatory = Bool(
        default=True
    )
    output_directory = Directory(
        exists=True,
    )


class SmoothOutputSpec(TraitedSpec):
    fmri_smoothed = ImageFile(
        desc='Smoothed fMRI file'
    )


class Smooth(SimpleInterface):
    input_spec = SmoothInputSpec
    output_spec = SmoothOutputSpec

    def _run_interface(self, runtime):
        if exists(self.inputs.fmri_prep):
            img = load(self.inputs.fmri_prep)
            smoothed = smooth_img(img, fwhm=6)
            et = explode_into_entities(self.inputs.fmri_prep)
            et.overwrite("desc", et["desc"] + "Smoothed" if et["desc"] else "Smoothed")
            self._results['fmri_smoothed'] = join(
                self.inputs.output_directory,
                et.build_filename())
            save(smoothed, self._results['fmri_smoothed'])
        elif self.inputs.is_file_mandatory:
            raise FileExistsError(f"Mandatory fMRI image file doesn't exists (input arg {self.inputs.fmri_prep})")
        return runtime
