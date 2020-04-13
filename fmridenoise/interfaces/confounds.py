import json
import os

import pandas as pd
import numpy as np

from typing import List
from traits.trait_types import Dict, Str, List, Directory
from nipype.interfaces.base import (BaseInterfaceInputSpec, File, TraitedSpec, 
    SimpleInterface)


class ConfoundsInputSpec(BaseInterfaceInputSpec):
    pipeline = Dict(
        mandatory=True,
        desc="Denoising pipeline")
    conf_raw = File(
        exist=True,
        mandatory=True,
        desc="Confounds table")
    conf_json = File(
        exist=True,
        mandatory=True,
        desc="Details aCompCor")
    subject = Str(
        mandatory=True,
        desc="Subject name")
    task = Str(
        mandatory=True,
        desc="Task name")
    session = Str(
        mandatory=False,
        desc="Session name")
    output_dir = Directory(
        exists=True,
        mandatory=True,
        desc="Output path")


class ConfoundsOutputSpec(TraitedSpec):
    conf_prep = File(
        exists=True,
        desc="Preprocessed confounds table")
    conf_summary = File(
        exists=True,
        desc="Confounds summary JSON")


class Confounds(SimpleInterface):
    input_spec = ConfoundsInputSpec
    output_spec = ConfoundsOutputSpec

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.conf_raw = pd.read_csv(self.inputs.conf_raw, sep='\t')
        with open(self.inputs.conf_json, 'r') as json_file:
            self.conf_json = json.load(json_file)

        self.n_volumes = len(self.conf_raw)

        self.conf_prep = pd.DataFrame()


    @property
    def conf_filename(self):
        return self.inputs.conf_raw.replace(
            'regressors.tsv',
            f"pipeline-{self.inputs.pipeline['name']}"
            ) 


    def _retain(self, regressor_names: List(str)):
        '''Copies selected regressors from conf_raw to conf_prep.'''
        if regressor_names:
            self.conf_prep = pd.concat((
                self.conf_prep,
                self.conf_raw[regressor_names]
            ))


    def _filter_tissue_signals(self):
        '''...'''
        tissue_regressors = []
        for confound, setting in self.inputs.pipeline['confounds'].items():
            
            if confound in ('white_matter', 'csf', 'global_signal') and setting:
                tissue_regressors.append(confound)
                
                if isinstance(setting, dict):
                    for transform, include in setting.items():
                        if include:
                            tissue_regressors.append(f'{confound}_{transform}')
        
        self._retain(tissue_regressors)


    def _filter_motion_parameters(self):
        '''...'''
        hmp_regressors = []
        hmp_names = [f'{type_}_{axis}' 
                     for type_ in ('trans', 'rot') 
                     for axis in ('x', 'y', 'z')]

        setting = self.inputs.pipeline['confounds']['motion']
        
        if setting:
            hmp_regressors.extend(hmp_names)

            if isinstance(setting, dict):
                for transform, include in setting.items():
                    if include:
                        hmp_regressors.extend(f'{hmp}_{transform}' 
                                            for hmp in hmp_names)
        
        self._retain(hmp_regressors)


    def _filter_acompcors(self):
        '''...'''
        if not self.inputs.pipeline['confounds']['acompcor']:
            return

        acompcor_regressors = []
        for mask in ('CSF', 'WM'):
            acompcors = {
                (name, dict_['VarianceExplained']) 
                for name, dict_ in self.conf_json.items()
                if dict_.get('Retained') and dict_.get('Mask') == mask 
                }
            acompcors = sorted(acompcors, key=lambda tpl: tpl[1], reverse=True)
            acompcor_regressors.extend(acompcor[0] for acompcor in acompcors[:5])

        self._retain(acompcor_regressors)


    def _create_spike_regressors(self):
        '''...'''
        if not self.inputs.pipeline['spikes']:
            return

        fd_th = self.inputs.pipeline['spikes']['fd_th']
        dvars_th = self.inputs.pipeline['spikes']['dvars_th']

        outliers = (self.conf_raw['framewise_displacement'] > fd_th) \
                 | (self.conf_raw['std_dvars'] > dvars_th) 
        outliers = list(outliers[outliers].index)

        if outliers:
            spikes = np.zeros((self.n_volumes, len(outliers)))
            for i, outlier in enumerate(outliers):
                spikes[outlier, i] = 1.
                
            conf_spikes = pd.DataFrame(
                data=spikes, 
                columns=[f'motion_outlier_{i:02}' for i in range(len(outliers))]
                )

            self.conf_prep = pd.concat((
                self.conf_prep,
                conf_spikes
            ))
        
        self.n_spikes = len(outliers)


    def _create_summary_dict(self):
        '''...'''
        self.conf_summary = {
            'subject': self.inputs.subject,
            'task': self.inputs.task,
            'mean_fd': self.conf_raw["framewise_displacement"].mean(),
            'max_fd': self.conf_raw["framewise_displacement"].max(),
            'n_conf': len(self.conf_prep.columns)
        }

        if self.inputs.pipeline['spikes']:
            self.conf_summary['n_spikes'] = self.n_spikes 
            self.conf_summary['perc_spikes'] = self.n_spikes / self.n_volumes * 100
            include = inclusion_check(
                n_timepoints=self.n_volumes, 
                mean_fd=self.conf_raw["framewise_displacement"].mean(),
                max_fd=self.conf_raw["framewise_displacement"].max(),
                n_spikes=self.n_spikes,
                fd_th=self.inputs.pipeline['spikes']['fd_th']
            )
            self.conf_summary['include'] = include  #TODO: Should this be calculated only if spikes are included?

        if self.inputs.session:
            self.conf_summary["session"] = str(self.inputs.session)


    def _run_interface(self, runtime):

        self._filter_motion_parameters()
        self._filter_tissue_signals()
        self._filter_acompcors()
        self._create_spike_regressors()
        self._create_summary_dict()

        self.conf_prep.to_csv(self.conf_filename + '.tsv', sep='\t', index=False)
        with open(self.conf_filename + '.json', 'w') as f:
            json.dump(self.conf_summary, f)

        self._results['conf_prep'] = self.conf_filename + '.tsv'
        self._results['conf_summary'] = self.conf_filename + '.json'

        return runtime


def inclusion_check(n_timepoints, mean_fd, max_fd, n_spikes, fd_th): #TODO convert to instance method
    """
    Checking if participant is recommended to be excluded from analysis
    based on motion parameters and spikes regressors.

    Inputs
    -------

    n_timepoints: number of timepoints
    mean_fd: mean framewise_displacement (FD)
    max_fd: maximum FD
    n_spikes: number of spikes
    fd_th: threshold for mean FD

    Outputs
    -------

    returns 0 if subject should be excluded due to head motion
    or 1 if there is no reason to exclude subject based on submitted threshold.

    """
    if mean_fd > fd_th:
        return 0
    elif max_fd > 5:
        return 0
    elif n_spikes/n_timepoints > 0.20:
        return 0
    else:
        return 1


class GroupConfoundsInputSpec(BaseInterfaceInputSpec):
    conf_summary_json_files = List(
        File(exists=True),
        mandatory=True,
        desc="Confounds summary")
    output_dir = Directory(          # needed to save data in other directory
        mandatory=True,
        desc="Output path")     # TODO: Implement temp dir
    task = Str(
        mandatory=True,
        desc="Task name")
    session = Str(
        mandatory=False,
        desc="Session name")
    pipeline_name = Str(mandatory=True,
                        desc="Pipeline name")


class GroupConfoundsOutputSpec(TraitedSpec):
    group_conf_summary = File(
        exists=True,
        desc="Confounds summary")


class GroupConfounds(SimpleInterface):
    input_spec = GroupConfoundsInputSpec
    output_spec = GroupConfoundsOutputSpec

    def _run_interface(self, runtime):
        group_conf_summary = pd.DataFrame()

        for summary_json_file in self.inputs.conf_summary_json_files:
            with open(summary_json_file, 'r') as f:
                group_conf_summary = group_conf_summary.append(pd.DataFrame.from_dict(json.load(f)))
        if self.inputs.session:
            base =  f"ses-{self.inputs.session}_task-{self.inputs.task}_pipeline-{self.inputs.pipeline_name}_groupConfSummary.tsv"
        else:
            base =  f"task-{self.inputs.task}_pipeline-{self.inputs.pipeline_name}_groupConfSummary.tsv"
        fname = os.path.join(self.inputs.output_dir, base)
        assert not os.path.exists(fname)
        group_conf_summary.to_csv(fname, sep='\t', index=False)
        self._results['group_conf_summary'] = fname
        return runtime
