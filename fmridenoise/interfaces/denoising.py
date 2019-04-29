from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )

import nibabel as nb
import os
import pandas as pd
from nilearn.image import clean_img


class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_prep = File(exists=True,
                     desc='Preprocessed fMRI file',
                     mandatory=True)
    conf_prep = File(exists=True,
                     desc='Confound file',
                     mandatory=True)
    output_dir = File(desc='Output path')


class DenoiseOutputSpec(TraitedSpec):
    fmri_denoised = File(exists=True,
                         desc='Denoised fMRI file',
                         mandatory=True)


class Denoise(SimpleInterface):
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.fmri_prep
        img = nb.load(fname)
        cname = self.inputs.conf_prep
        conf = pd.read_csv(cname, delimiter='\t')

        denoised_img = clean_img(img, confounds=conf)

        _, base, _ = split_filename(fname)
        nb.save(denoised_img, f'{self.inputs.output_dir}/{base}_denoised.nii')
        self._results['fmri_denoised'] = os.path.abspath(base + '_denoised.nii')

        return runtime
