from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

import nibabel as nb
import numpy as np
import os
import pandas as pd

class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_preprocessed = File(exists=True, desc='preprocessed fMRI file', mandatory=True)
    confounds = File(exists=True, desc='confound file', mandatory=True)

class DenoiseOutputSpec(TraitedSpec):
    fmri_denoised = File(exists=True, desc='denoised fMRI file', mandatory=True)

class Denoise(BaseInterface):
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.fmri_preprocessed
        img = nb.load(fname)
        cname = self.inputs.confounds
        conf = pd.read_csv(cname, delimiter = '\t')
        conf = conf.iloc[:,:3].values

        denoised_img = clean_img(img, confounds=conf)

        _, base, _ = split_filename(fname)
        nb.save(denoised_img, base + '_denoised.nii')

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.fmri_preprocessed
        _, base, _ = split_filename(fname)
        #outputs["denoised_fmri"] = os.path.abspath(base + '_denoised.nii')
        return outputs
