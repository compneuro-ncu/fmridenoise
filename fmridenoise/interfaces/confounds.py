import pandas as pd
from traits.trait_types import Dict, Str, List, Directory
from nipype.interfaces.base import BaseInterfaceInputSpec, File, TraitedSpec, SimpleInterface
from nipype.utils.filemanip import split_filename
from fmridenoise.utils.confound_prep import prep_conf_df
from fmridenoise.utils.utils import split_suffix
from os.path import join
import json
import os


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
    conf_summary_json_file = File(
        exists=True,
        desc="Confounds summary")


class Confounds(SimpleInterface):
    input_spec = ConfoundsInputSpec
    output_spec = ConfoundsOutputSpec

    def _run_interface(self, runtime):

        pipeline_name = self.inputs.pipeline['name']
        fname = self.inputs.conf_raw
        json_path = self.inputs.conf_json

        conf_df_raw = pd.read_csv(fname, sep='\t')

        # Load aCompCor list

        with open(json_path, 'r') as json_file:
            js = json.load(json_file)

        a_comp_cor_csf, a_comp_cor_wm = ([] for _ in range(2))

        for i in js.keys():
            if i.startswith('a_comp_cor'):
                if js[i]['Mask'] == 'CSF' and js[i]['Retained']:
                    a_comp_cor_csf.append(i)

                if js[i]['Mask'] == 'WM' and js[i]['Retained']:
                    a_comp_cor_wm.append(i)

        a_comp_cor = a_comp_cor_csf[:5] + a_comp_cor_wm[:5]

        # Preprocess confound table according to pipeline
        conf_df_prep = prep_conf_df(conf_df_raw, self.inputs.pipeline, a_comp_cor)

        # Create new filename and save
        path, base, _ = split_filename(fname)  # Path can be removed later
        base, suffix = split_suffix(base)
        fname_prep = join(self.inputs.output_dir, f"{base}_pipeline-{pipeline_name}_conf.tsv")  # use output path
        conf_df_prep.to_csv(fname_prep, sep='\t', index=False)

        # Creates dictionary with summary measures
        n_spikes = conf_df_prep.filter(regex='spike', axis=1).sum().sum()
        mean_fd = conf_df_raw["framewise_displacement"].mean()
        max_fd = conf_df_raw["framewise_displacement"].max()
        n_timepoints = len(conf_df_raw)

        conf_summary = { # TODO: Why there are lists in this dict and not a simple types?
                        "subject": [str(self.inputs.subject)],
                        "task": [str(self.inputs.subject)],
                        "mean_fd": [float(mean_fd)],
                        "max_fd": [float(max_fd)],
                        "n_spikes": [float(n_spikes)],
                        "perc_spikes": [float((n_spikes/n_timepoints)*100)],
                        "n_conf": [float(len(conf_df_prep.columns))],
                        "include": [float(inclusion_check(n_timepoints, mean_fd, max_fd, n_spikes, 0.2))]
                        }
        if self.inputs.session:
            conf_summary["session"] = [str(self.inputs.session)]
        conf_summary_json_file_name = join(self.inputs.output_dir,
                                           f"{base}_pipeline-{pipeline_name}_summaryDict.json")
        assert not os.path.exists(conf_summary_json_file_name)
        with open(conf_summary_json_file_name, 'w') as f:
            json.dump(conf_summary, f)
        self._results['conf_prep'] = fname_prep
        self._results['conf_summary_json_file'] = conf_summary_json_file_name

        return runtime


def inclusion_check(n_timepoints, mean_fd, max_fd, n_spikes, fd_th):
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
        fname = join(self.inputs.output_dir, base)
        assert not os.path.exists(fname)
        group_conf_summary.to_csv(fname, sep='\t', index=False)
        self._results['group_conf_summary'] = fname
        return runtime
