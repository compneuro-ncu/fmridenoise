import os
import math
import json
import shutil
import nipype as ni


pipeline_null = {
    'name': 'Null',
    'description': '',
    'confounds': {
        'white_matter': {
            'raw': False,
            'derivative1': False,
            'power2': False,
            'derivative1_power2': False
        },
        'csf': {
            'raw': False,
            'derivative1': False,
            'power2': False,
            'derivative1_power2': False
        },
        'global_signal': {
            'raw': False,
            'derivative1': False,
            'power2': False,
            'derivative1_power2': False
        },
        'motion': {
            'raw': False,
            'derivative1': False,
            'power2': False,
            'derivative1_power2': False
        },
        'acompcor': False
    },
    'aroma': False,
    'spikes': False
}


def confound_filename(sub, task, ses, ext):
    '''Create proper filename for raw confounds given BIDS entity.'''
    sub_substr = f'sub-{sub}_'
    ses_substr = f'ses-{ses}_' if ses else ''
    task_substr = f'task-{task}_'
    return f'{sub_substr}{ses_substr}{task_substr}desc-confounds_regressors.{ext}'


def fmri_prep_filename(sub, ses, task, aroma):
    '''Create proper filename for preprocessed fmri file given BIDS entity.'''
    sub_substr = f'sub-{sub}_'
    ses_substr = f'ses-{ses}_' if ses else ''
    task_substr = f'task-{task}_'
    desc_substr =  'desc-smoothAROMAnonaggr_' if aroma else 'desc-preproc_'
    return f'{sub_substr}{ses_substr}{task_substr}' + \
           f'space-MNI152NLin2009cAsym_{desc_substr}bold.nii.gz'
