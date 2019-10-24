from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec,
    ImageFile, SimpleInterface, Directory)
from nibabel import load, save
from nilearn.image import smooth_img
from nipype.utils.filemanip import split_filename
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
            _, base, _ = split_filename(self.inputs.fmri_prep)
            self._results['fmri_smoothed'] = join(
                self.inputs.output_directory,
                f'{base}_smoothed.nii.gz')
            save(smoothed, self._results['fmri_smoothed'])
        elif self.inputs.is_file_mandatory:
            raise FileExistsError(f"Mandatory fMRI image file doesn't exists (input arg {self.inputs.fmri_prep})")
        return runtime