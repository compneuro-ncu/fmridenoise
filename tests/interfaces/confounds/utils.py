import pandas as pd
import numpy as np
import json

pipeline_null = {
    'name': '',
    'description': '',
    'confounds': {
        'wm': False,
        'csf': False,
        'gs': False,
        'motion': False,
        'acompcor': False
        },
    'aroma': False,
    'spikes': False
}

def confound_filename(sub, task, ses, ext):
    sub_substr = f'sub-{sub}_'
    ses_substr = f'ses-{ses}_' if ses else ''
    task_substr = f'task-{task}_'
    return f'{sub_substr}{ses_substr}{task_substr}desc-confounds_regressors.{ext}'

class ConfoundsGenerator:

    _params = {
        'csf_mean': 4500,
        'csf_std': 30,
        'gs_mean': 4600,
        'gs_std': 30,
        'wm_mean': 4700,
        'wm_std': 30,
        'dvars_slope': 30,
        'dvars_intercept': 20,
        'dvars_noise': 6,
        'tcompcor_meta_std': 0.05,
        'acompcor_meta_std': 0.05,
        'aroma_std': 0.05,
        'trans_meta_std': 0.02,
        'trans_meta_mean': 0.005,
        'rot_meta_std': 0.001,
        'rot_meta_mean': 0,
        'sv_slope': 8000
    }

    def __init__(self, n_volumes=20, *, n_tcompcor=10, n_acompcor=300, 
                 n_aroma=0, seed=0):

        self._n_volumes = n_volumes
        self._n_tcompcor = n_tcompcor
        self._n_acompcor = n_acompcor
        self._n_aroma = n_aroma

        self._df = pd.DataFrame()
        self._meta = {}

        if seed is not None:
            np.random.seed(seed)

        self._create()

    @property
    def confounds(self):
        return self._df
    
    @property
    def confounds_meta(self):
        return self._meta
    
    @property
    def mean_fd(self):
        return self.confounds['framewise_displacement'].mean()
    
    @property
    def max_fd(self):
        return self.confounds['framewise_displacement'].max()
    
    @property
    def relevant_acompcors(self):
        '''Returns computed list of 10 acompcor regressors (5 for both wm and csf) with highest 
        explained variance'''
        if self._n_acompcor < 15:
            return []

        acompcors_filtered = []
        for tissue in ['CSF', 'WM']:
            acompcors = [(key, val['VarianceExplained']) 
                         for key, val in self.confounds_meta.items() 
                         if val.get('Mask') == tissue]
            acompcors.sort(key=lambda x: x[1], reverse=True)
            acompcors = [acompcor[0] for acompcor in acompcors[:5]]
            acompcors_filtered.extend(acompcors)
            
        return acompcors_filtered

    def get_outlier_scans(self, fd_thr, dvars_thr):
        outliers = (self._df['framewise_displacement'] >= fd_thr) | (self._df['std_dvars'] >= dvars_thr)
        return list(outliers[outliers].index)

    def _create_tissue_signals(self):
        tissue_signals = {}
        tissue_signals['csf'] = (self._params['csf_mean'] 
                                 + self._params['csf_std'] 
                                 * np.random.randn(self._n_volumes, ))
        tissue_signals['white_matter'] = (self._params['wm_mean'] 
                                          + self._params['wm_std'] 
                                          * np.random.randn(self._n_volumes, ))
        tissue_signals['global_signal'] = (self._params['gs_mean'] 
                                           + self._params['gs_std'] 
                                           * np.random.randn(self._n_volumes, ))


        for conf_name, signal in tissue_signals.items():
            self._df[conf_name] = signal
            self._df[conf_name + '_derivative1'] = np.diff(signal, prepend=np.nan)
            self._df[conf_name + '_derivative1_power2'] = np.power(np.diff(signal, prepend=np.nan), 2)

    def _create_motion_params(self):
        motion_params = {}
        for axis in 'xyz':
            motion_params['trans_' + axis] = np.cumsum(
                np.random.randn(self._n_volumes) 
                * (self._params['trans_meta_mean'] 
                   + np.random.rand() * self._params['trans_meta_std']))
            motion_params['rot_' + axis] = np.cumsum(
                np.random.randn(self._n_volumes) 
                * (self._params['rot_meta_mean'] 
                   + np.random.rand() * self._params['rot_meta_std']))

        for conf_name, signal in motion_params.items():
            self._df[conf_name] = signal
            self._df[conf_name + '_derivative1'] = np.diff(signal, prepend=np.nan)
            self._df[conf_name + '_derivative1_power2'] = np.power(np.diff(signal, prepend=np.nan), 2)

    def _create_framewise_displacement(self):
        self._df['framewise_displacement'] = (
            self._df['trans_x'].diff().abs() + 
            self._df['trans_y'].diff().abs() + 
            self._df['trans_z'].diff().abs() +
            50 * self._df['rot_x'].diff().abs() + 
            50 * self._df['rot_y'].diff().abs() + 
            50 * self._df['rot_z'].diff().abs()
        )

    def _create_dvars(self):
        self._df['dvars'] = (self._params['dvars_slope'] * self._df['framewise_displacement'] 
                          + self._params['dvars_intercept'] 
                          + self._params['dvars_noise'] * np.random.randn(self._n_volumes))
        # Note: this is not nipype implementation of std_dvars
        self._df['std_dvars'] = self._df['dvars'] / self._df['dvars'].mean()

    def _create_tcompcors(self):
        for i in range(self._n_tcompcor):
            self._df[f't_comp_cor_{i:02}'] = (self._params['tcompcor_meta_std'] 
                                              * np.random.randn() 
                                              * np.random.randn(self._n_volumes))
            self._meta[f't_comp_cor_{i:02}'] = {
                'Method': 'tCompCor',
                'Retained': True
            }
            
    def _create_acompcors(self):
        variance_acompcor = (np.arange(self._n_acompcor, 0, -1) 
                             / np.sum(np.arange(self._n_acompcor, 0, -1)))
        variance_acompcor_cum = np.cumsum(variance_acompcor)
        
        for i in range(self._n_acompcor):
            self._df[f'a_comp_cor_{i:02}'] = (self._params['acompcor_meta_std'] 
                                              * np.random.randn() 
                                              * np.random.randn(self._n_volumes)) 
            self._meta[f'a_comp_cor_{i:02}'] = {
                'CumulativeVarianceExplained': variance_acompcor_cum[i],
                'Method': 'tCompCor',
                'Mask': ['combined', 'CSF', 'WM'][i%3],
                'Retained': True,
                'SingularValue': self._params['sv_slope'] * variance_acompcor[i],
                'VarianceExplained': variance_acompcor[i]
            }            

    def _create_cosine_functions(self):
        hfcut = 1 / 128  # low pass filter  
        t_r = 2          # repetition time
        n_cosine = int(np.floor(2 * self._n_volumes * hfcut * t_r))        
        for i in range(n_cosine):
            self._df[f'cosine{i:02}'] = np.cos(np.linspace(0, (i+1)*np.pi, 
                                                           num=self._n_volumes))

    def _create_motion_outliers(self):
        outlier_scans = self.get_outlier_scans(fd_thr=0.5, dvars_thr=1.5)
        for i, scan in enumerate(outlier_scans):
            spike_regressor = np.zeros((self._n_volumes, ))
            spike_regressor[scan] = 1.
            self._df[f'motion_outlier_{i:02}'] = spike_regressor

    def _create_aroma_regressors(self):
        for i in range(self._n_aroma):
            self._df[f'aroma_motion_{i:02}'] = (self._params['aroma_std'] 
                                                * np.random.randn() 
                                                * np.random.randn(self._n_volumes))

    def meta_to_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self._meta, f, sort_keys=True, indent=4, separators=(',', ': '))

    def _create(self):
        self._create_tissue_signals()
        self._create_motion_params()
        self._create_framewise_displacement()    
        self._create_dvars()
        self._create_tcompcors()
        self._create_acompcors()
        self._create_cosine_functions()
        self._create_motion_outliers()
        self._create_aroma_regressors()