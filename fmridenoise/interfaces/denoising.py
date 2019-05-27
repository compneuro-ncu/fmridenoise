from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    )
from traits.trait_types import File, Float
from nipype.utils.filemanip import split_filename
import nibabel as nb
import os
import pandas as pd
from nilearn.image import clean_img
import numpy as np


class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_prep = File(exists=True,
                     desc='Preprocessed fMRI file',
                     mandatory=True)
    conf_prep = File(exists=True,
                     desc='Confound file',
                     mandatory=True)
    output_dir = File(desc='Output path')
    high_pass = Float(desc="High-pass filter")
    low_pass = Float(desc="Low-pass filter")


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

        try:
            conf = pd.read_csv(cname, delimiter='\t')
            conf = conf.values
        except pd.errors.EmptyDataError:  # In case of null pipeline
            conf = None

        #conf = pd.read_csv(cname, delimiter='\t')



        denoised_img = clean_img(img,
                                 confounds=conf,
                                 high_pass=self.inputs.high_pass,
                                 low_pass=self.inputs.low_pass,
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

    #conf= ut.load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    confpath = "/home/finc/Dropbox/Projects/fitlins/BIDS/derivatives/fmriprep/sub-09/func/" + \
               "sub-09_task-rhymejudgment_desc-confounds_regressors.tsv"

    dn = Denoise()
    dn.inputs.fmri_prep = '/media/finc/Elements/BIDS_pseudowords/BIDS/derivatives/fmriprep/sub-01/func/sub-01_task-rhymejudgment_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
    #dn.inputs.low_pass = 0.08
    #dn.inputs.high_pass = 0.008
    #dn.inputs.conf_prep = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/sub-01_task-rhymejudgment_desc-confounds_regressors_36_parameters_spikes_prep.tsv'
    #dn.inputs.conf_prep = '/media/finc/Elements/BIDS_pseudowords_short/BIDS/derivatives/fmridenoise/sub-01/sub-01_task-rhymejudgment_desc-confounds_regressors_36_parameters_spikes_prep_suff.tsv'
                          #'sub-01_task-rhymejudgment_desc-confounds_regressors_null_prep_suff.tsv'

    dn.inputs.conf_prep = '/media/finc/Elements/BIDS_pseudowords_short/BIDS/derivatives/fmridenoise/sub-01/sub-01_task-rhymejudgment_desc-confounds_regressors_null_prep_suff.tsv'


    dn.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    results = dn.run()

    print(results.outputs)
