from nilearn.image import clean_img
from nipype.utils.filemanip import split_filename
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    ImageFile, File, Directory, traits)
import nibabel as nb
import pandas as pd
from fmridenoise.utils.utils import split_suffix
from os.path import exists


class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_prep = ImageFile(
        default=None,
        desc='Preprocessed fMRI file',
        mandatory=False
    )

    fmri_prep_aroma = ImageFile(
        default=None,
        desc='ICA-Aroma preprocessed fMRI file',
        mandatory=False
    )

    conf_prep = File(
        exists=True,
        desc="Confound file",
        mandatory=True
    )

    pipeline = traits.Dict(
        desc="Denoising pipeline",
        mandatory=True)

    task = traits.Str(
        desc="Task name",
        mandatory=True
    )

    tr_dict = traits.Dict(
        desc="dictionary of tr for all tasks",
        mandatory=True
    )

    output_dir = Directory(
        exists=True,
        desc="Output path",
        mandatory=True
    )

    high_pass = traits.Float(
        desc="High-pass filter",
        mandatory=True
    )

    low_pass = traits.Float(
        desc="Low-pass filter",
        mandator=True
    )


class DenoiseOutputSpec(TraitedSpec):
    fmri_denoised = File(
        exists=True,
        desc='Denoised fMRI file',
        mandatory=True
    )


class Denoise(SimpleInterface):
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec

    def _run_interface(self, runtime):
        assert self.inputs.fmri_prep is not None or self.inputs.fmri_prep_aroma is not None, \
            "Both fmri_prep and fmri_prep_aroma is missing"
        pipeline_name = self.inputs.pipeline['name']
        pipeline_aroma = self.inputs.pipeline['aroma']
        if pipeline_aroma:
            assert exists(str(self.inputs.fmri_prep_aroma)), \
                f"No such required fmri_prep_aroma file as: {self.inputs.fmri_prep_aroma}"
            img = nb.load(self.inputs.fmri_prep_aroma)
 
        else:
            assert exists(str(self.inputs.fmri_prep)), \
                f"No such required fmri_prep file as: {self.inputs.fmri_prep}"
            img = nb.load(self.inputs.fmri_prep)
        # Handle possibility of null pipeline
        try:
            conf = pd.read_csv(self.inputs.conf_prep,
                               delimiter='\t',
                               #low_memory=False,
                               #engine='python'
                               )
            conf = conf.values
        except pd.errors.EmptyDataError:
            conf = None

        # Determine proper TR
        if self.inputs.task in self.inputs.tr_dict:
            tr = self.inputs.tr_dict[self.inputs.task]
        else:
            raise KeyError(f'{self.inputs.task} TR not found in tr_dict')

        denoised_img = clean_img(
            img,
            confounds=conf,
            high_pass=self.inputs.high_pass,
            low_pass=self.inputs.low_pass,
            t_r=tr
        )

        _, base, _ = split_filename(self.inputs.fmri_prep)
        base, _ = split_suffix(base)
        denoised_file = f'{self.inputs.output_dir}/pipeline-{pipeline_name}_{base}_Denoised.nii.gz'

        nb.save(denoised_img, denoised_file)

        self._results['fmri_denoised'] = denoised_file

        return runtime
