from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )
from nipype.utils.filemanip import split_filename
import nibabel as nb
import os
import pandas as pd
from nilearn.image import clean_img
import numpy as np
from fmridenoise.utils.confound_prep import prep_conf_df




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
        conf = conf.values

        denoised_img = clean_img(img,
                                 confounds=conf,
                                 low_pass=0.08,  # TODO: load filter from file
                                 high_pass=0.008,  # TODO: load filter from file
                                 t_r=2,  # TODO: load TR from pieline description
                        )

        _, base, _ = split_filename(fname)
        denoised_file = f'{self.inputs.output_dir}/{base}_denoised.nii'

        nb.save(denoised_img, denoised_file)
        self._results['fmri_denoised'] = denoised_file

        return runtime


# --- TESTS

if __name__ == '__main__':
    from nipype import Node
    import utils as ut

    prep_conf = Node(Denoise(), name="Denoise")

    conf= ut.load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    confpath = "/home/finc/Dropbox/Projects/fitlins/BIDS/derivatives/fmriprep/sub-09/func/" + \
               "sub-09_task-rhymejudgment_desc-confounds_regressors.tsv"

    dn = Denoise()
    dn.inputs.fmri_prep = '/media/finc/Elements/BIDS_pseudowords/BIDS/derivatives/fmriprep/sub-01/func/sub-01_task-rhymejudgment_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    dn.inputs.low_pass = 0.08
    dn.inputs.high_pass = 0.008
    dn.inputs.conf_prep = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/sub-01_task-rhymejudgment_desc-confounds_regressors_36_parameters_spikes_prep.tsv'
    dn.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    results = dn.run()

    print(results.outputs)
