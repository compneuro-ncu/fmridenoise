import pandas as pd
import nibabel as nb
import os

from traits.trait_base import _Undefined
from nilearn.image import clean_img
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    ImageFile, File, Directory, traits)

from fmridenoise.utils.entities import explode_into_entities


class DenoiseInputSpec(BaseInterfaceInputSpec):
    fmri_prep = ImageFile(
        mandatory=False,
        exists=True,
        desc='Preprocessed fMRI file'
        )
    fmri_prep_aroma = ImageFile(
        mandatory=False,
        exists=True,
        desc='ICA-Aroma preprocessed fMRI file',
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
    task = traits.Str(
        mandatory=True,
        desc='Task name'
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
        desc='Low cut-off frequency in Hertz'
    )


class DenoiseOutputSpec(TraitedSpec):
    fmri_denoised = File(
        mandatory=True,
        exists=True,
        desc='Denoised fMRI file',
    )


class Denoise(SimpleInterface):
    ''' Denoise functional images using filtered confounds.

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
    '''
    input_spec = DenoiseInputSpec
    output_spec = DenoiseOutputSpec

    def _validate_fmri_prep_files(self):
        '''Check if correct file is provided according to aroma option in 
        pipeline dictionary.
        
        Creates:
            _fmri_file (attibute): 
                preprocessed fmri file (either with or without aroma)
        '''
        if not self.inputs.pipeline['aroma']: 
            if isinstance(self.inputs.fmri_prep, _Undefined):
                raise FileNotFoundError('for pipeline using aroma ' + \
                                        'file fmri_prep_aroma is required')
            self._fmri_file = self.inputs.fmri_prep     
        else:
            if isinstance(self.inputs.fmri_prep_aroma, _Undefined):
                raise FileNotFoundError('for pipeline without aroma ' + \
                                        'file fmri_prep is required')
            self._fmri_file = self.inputs.fmri_prep_aroma             

    def _create_fmri_denoised_filename(self):
        '''Creates proper filename for fmri_denoised file.
        
        Creates:
            _fmri_denoised_fname:
                Full path to denoised fmri file.

        Note that this method requires _fmri_file attribute, so it has to be
        called after _validate_fmri_prep_files.        
        '''
        et = explode_into_entities(self._fmri_file)
        et["pipeline"] = self.inputs.pipeline["name"]
        et.overwrite("desc", "denoised")
        et.overwrite("suffix", "bold")
        et.overwrite("extension", "nii.gz")
        self._fmri_denoised_fname = os.path.join(
            self.inputs.output_dir,
            et.build_filename()
        )

    def _load_confouds(self):
        '''Load confounds from tsv file. If confounds is empty file (in case of 
        null pipeline) confounds keyword argument for clean_img should be None.
        
        Creates:
            _confounds (attribute):
                Either None (for null pipeline) or np.ndarray of confounds if 
                conf_prep is not empty.
        '''
        try:
            self._confounds = pd.read_csv(
                self.inputs.conf_prep, delimiter='\t').values
        except pd.errors.EmptyDataError:
            self._confounds = None

    def _validate_filtering(self):
        '''Validate input arguments related to temporal filtering.
        
        Creates:
            _filtering_kwargs (attribute):
                Dictionary of optional keyword arguments passed to clean_img.
                Empty if no temporal filtering is requested.         
        '''
        self._filtering_kwargs = dict()
        if not isinstance(self.inputs.low_pass, _Undefined):
            self._filtering_kwargs.update(low_pass=self.inputs.low_pass)
        if not isinstance(self.inputs.high_pass, _Undefined):
            self._filtering_kwargs.update(high_pass=self.inputs.high_pass)
        if self._filtering_kwargs:
            self._filtering_kwargs.update(
                t_r=self.inputs.tr_dict[self.inputs.task])

    def _run_interface(self, runtime):
        self._validate_fmri_prep_files()
        self._validate_filtering()
        self._load_confouds()
        self._create_fmri_denoised_filename()

        fmri_denoised = clean_img(
            nb.load(self._fmri_file), 
            confounds=self._confounds, 
            **self._filtering_kwargs)

        nb.save(fmri_denoised, self._fmri_denoised_fname)
        self._results['fmri_denoised'] = self._fmri_denoised_fname

        return runtime
