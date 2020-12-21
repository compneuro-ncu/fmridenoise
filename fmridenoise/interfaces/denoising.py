from os.path import join, exists
import pandas as pd
import nibabel as nb
from traits.trait_base import Undefined
from nilearn.image import clean_img
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    ImageFile, File, Directory, traits)
from fmridenoise.utils.entities import parse_file_entities, build_path


class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_prep = ImageFile(
        mandatory=False,
        exists=True,
        desc='Preprocessed fMRI file'
        )
    fmri_prep_aroma = ImageFile(
        mandatory=False,
        exists=True,
        desc='ICA-Aroma preprocessed fMRI file'
    )
    conf_prep = File(
        mandatory=True,
        exists=True,
        desc='Confounds file'
        )

    pipeline = traits.Dict(
        mandatory=True,
        desc='Denoising pipeline'
        )
    output_dir = Directory(
        exists=True,
        desc='Output path',
        mandatory=True
    )
    tr_dict = traits.Dict(
        mandatory=False,
        desc='TR values for all tasks'
    )
    high_pass = traits.Float(
        mandatory=False,
        desc='High cut-off frequency in Hertz'
    )
    low_pass = traits.Float(
        mandatory=False,
        desc="Low-pass filter"
    )
    smoothing = traits.Bool(
        mandatory=False,
        desc='Low cut-off frequency in Hertz'
    )


class DenoiseOutputSpec(TraitedSpec):
    fmri_denoised = File(
        mandatory=True,
        exists=True,
        desc='Denoised fMRI file',
    )


class Denoise(SimpleInterface):
    """ Denoise functional images using filtered confounds.

    This interface uses filtered confounds table and temporal (bandpass) 
    filtering to denoise functional images. It wraps around nilearn clean_img
    function to create and save denoised file. 

    At least one of two inputs should be passed to this interface depending on
    denoising strategy. If denoising assumes aroma, fmri_prep_aroma file should
    be provided, otherwise fmri_prep file should be provided.

    Temporal filtering can be requested by specifying either one or two optonal 
    inputs: low_pass and high_pass. These reflect cut-off values (in Hertz) for 
    low-pass and high-pass temporal filters. Note that if either low_pass or 
    high_pass argument is provided, tr_dict containing task name as key and task
    TR (in seconds) as value should also be provided (because in that case 
    clean_img requires TR). 

    Output filename reflecting denoised filename is created by adding suffix
        'pipeline-<pipeline_name>_desc-denoised_bold'
    to existing filename (desc-preproc is replaced with desc-denoised).
    """
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec
    fmri_denoised_pattern = "sub-{subject}[_ses-{session}]_task-{task}[_run-{run}]_space-{space}_pipeline-{pipeline}" \
                            "_desc-denoised_bold.nii.gz"

    def _validate_fmri_prep_files(self):
        """Check if correct file is provided according to aroma option in 
        pipeline dictionary.
        
        Creates:
            _fmri_file (attibute): 
                preprocessed fmri file (either with or without aroma)
        """
        if not self.inputs.pipeline['aroma']: 
            if self.inputs.fmri_prep is Undefined:
                raise FileNotFoundError('for pipeline using aroma ' + \
                                        'file fmri_prep_aroma is required')
            self._fmri_file = self.inputs.fmri_prep     
        else:
            if self.inputs.fmri_prep_aroma is Undefined:
                raise FileNotFoundError('for pipeline without aroma ' + \
                                        'file fmri_prep is required')
            self._fmri_file = self.inputs.fmri_prep_aroma
        return self._fmri_file

    def _load_confouds(self):
        """Load confounds from tsv file. If confounds is empty file (in case of 
        null pipeline) confounds keyword argument for clean_img should be None.
        
        Creates:
            _confounds (attribute):
                Either None (for null pipeline) or np.ndarray of confounds if 
                conf_prep is not empty.
        """
        try:
            self._confounds = pd.read_csv(
                self.inputs.conf_prep, delimiter='\t').values
        except pd.errors.EmptyDataError:
            self._confounds = None

    def _validate_filtering(self, task):
        """Validate input arguments related to temporal filtering.
        
        Creates:
            _filtering_kwargs (attribute):
                Dictionary of optional keyword arguments passed to clean_img.
                Empty if no temporal filtering is requested.         
        """
        self._filtering_kwargs = dict()
        if self.inputs.low_pass is not Undefined:
            self._filtering_kwargs.update(low_pass=self.inputs.low_pass)
        if self.inputs.high_pass is not Undefined:
            self._filtering_kwargs.update(high_pass=self.inputs.high_pass)
        if self._filtering_kwargs:
            self._filtering_kwargs.update(
                t_r=self.inputs.tr_dict[task])

    def _run_interface(self, runtime):

        fmri_file = self._validate_fmri_prep_files()
        entities = parse_file_entities(fmri_file)
        self._validate_filtering(entities['task'])
        self._load_confouds()
        entities = parse_file_entities(self._fmri_file)
        fmri_denoised = clean_img(
            nb.load(self._fmri_file), 
            confounds=self._confounds, 
            **self._filtering_kwargs)

        entities['pipeline'] = self.inputs.pipeline['name']
        fmri_denoised_fname = join(self.inputs.output_dir, build_path(entities, self.fmri_denoised_pattern, False))
        assert not exists(fmri_denoised_fname), f"Denoising is run twice at {self._fmri_file} " \
                                                f"with result {fmri_denoised_fname}"
        nb.save(fmri_denoised, fmri_denoised_fname)
        self._results['fmri_denoised'] = fmri_denoised_fname

        return runtime
