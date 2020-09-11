from bids.layout import parse_file_entities
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec,
    ImageFile, SimpleInterface, Directory)
from nibabel import load, save
from nilearn.image import smooth_img
from os.path import join, exists
from traits.trait_types import Bool

from fmridenoise.utils.entities import build_path


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
    smooth_file_pattern = "sub-{subject}[_ses-{session}]_task-{task}_space-{space}_desc-Smoothed_bold.nii.gz"

    def _run_interface(self, runtime):
        if exists(self.inputs.fmri_prep):
            img = load(self.inputs.fmri_prep)
            smoothed = smooth_img(img, fwhm=6)
            entities = parse_file_entities(self.inputs.fmri_prep)
            output_path = join(self.inputs.output_directory, build_path(entities, self.smooth_file_pattern, False))
            assert not exists(output_path), f"Smoothing is run twice at {output_path}"
            save(smoothed, output_path)
            self._results['fmri_smoothed'] = output_path
        elif self.inputs.is_file_mandatory:
            raise FileExistsError(f"Mandatory fMRI image file doesn't exists (input arg {self.inputs.fmri_prep})")
        return runtime
