import pandas as pd
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, SimpleInterface, \
    InputMultiObject
from nipype.utils.filemanip import split_filename
from fmridenoise.utils.confound_prep import prep_conf_df
from os.path import join
import json

class ConfoundsInputSpec(BaseInterfaceInputSpec):
    pipeline = traits.Dict(
        desc="Denoising pipeline",
        mandatory=True)
    conf_raw = File(
        exist=True,
        desc="Confounds table",
        mandatory=True)
    conf_json = File(
        exist=True,
        desc="Details aCompCor",
        mandatory=True)
    entities = traits.Dict(
        usedefault=True,
        desc='Per-file entities to include in filename')
    output_dir = File(          # needed to save data in other directory
        desc="Output path")     # TODO: Implement temp dir


class ConfoundsOutputSpec(TraitedSpec):
    conf_prep = File(
        exists=True,
        desc="Preprocessed confounds table")
    conf_summary = traits.Dict(
        exists=True,
        desc="Confounds summary")
    pipeline_name = traits.Str(desc="Name of denoising strategy")


class Confounds(SimpleInterface):
    input_spec = ConfoundsInputSpec
    output_spec = ConfoundsOutputSpec

    def _run_interface(self, runtime):

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
        fname_prep = join(self.inputs.output_dir, f"{base}_prep.tsv")  # use output path
        conf_df_prep.to_csv(fname_prep, sep='\t', index=False)

        # Creates dictionary with summary measures
        n_spikes = conf_df_prep.filter(regex='spike', axis=1).sum().sum()
        mean_fd = conf_df_raw["framewise_displacement"].mean()
        max_fd = conf_df_raw["framewise_displacement"].max()
        n_timepoints = len(conf_df_raw)

        conf_summary = {
                        "subject": [self.inputs.entities['subject']],
                        "session": [self.inputs.entities['session']],
                        "task": [self.inputs.entities['task']],
                        "mean_fd": [mean_fd],
                        "max_fd": [max_fd],
                        "n_spikes": [n_spikes],
                        "n_conf": [len(conf_df_prep.columns)],
                        "include_lib": [inclusion_check(n_timepoints, mean_fd, max_fd, n_spikes, 0.5)],
                        "include_con": [inclusion_check(n_timepoints, mean_fd, max_fd, n_spikes, 0.2)]
                        }

        self._results['conf_prep'] = fname_prep
        self._results['conf_summary'] = conf_summary
        self._results['pipeline_name'] = self.inputs.pipeline['name']

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
    conf_summary = traits.List(
        exists=True,
        desc="Confounds summary")

    output_dir = File(          # needed to save data in other directory
        desc="Output path")     # TODO: Implement temp dir

    pipeline_name = traits.List(mandatory=True)


class GroupConfoundsOutputSpec(TraitedSpec):
    group_conf_summary = File(
        exists=True,
        desc="Confounds summary")


class GroupConfounds(SimpleInterface):
    input_spec = GroupConfoundsInputSpec
    output_spec = GroupConfoundsOutputSpec

    def _run_interface(self, runtime):
        group_conf_summary = pd.DataFrame()

        for summary, pipeline_name in zip(self.inputs.conf_summary, self.inputs.pipeline_name):
            group_conf_summary = group_conf_summary.append(pd.DataFrame.from_dict(summary))
        fname = join(self.inputs.output_dir, f"{pipeline_name}_group_conf_summary.tsv")
        group_conf_summary.to_csv(fname, sep='\t', index=False)
        self._results['group_conf_summary'] = fname
        return runtime


if __name__ == '__main__':

    bids_dir = '/media/finc/Elements/zmien_nazwe'
    conf_json = '/media/finc/Elements/zmien_nazwe/derivatives/fmriprep/sub-01/ses-1/func/sub-01_ses-1_task-rest_desc-confounds_regressors.json'
    conf_raw = '/media/finc/Elements/zmien_nazwe/derivatives/fmriprep/sub-01/ses-1/func/sub-01_ses-1_task-rest_desc-confounds_regressors.tsv'

    from fmridenoise.utils.utils import load_pipeline_from_json

    pipeline = load_pipeline_from_json('/home/finc/Dropbox/Projects/fMRIDenoise/fmridenoise/fmridenoise/pipelines/pipeline-acomp_cor.json')
    entities = {'datatype': 'func', 'session': '1', 'subject': '01', 'task': 'rest'}

    conf = Confounds(
        conf_json=conf_json,
        conf_raw=conf_raw,
        pipeline=pipeline,
        entities=entities,
        output_dir='/media/finc/Elements/zmien_nazwe'
    )

    result = conf.run()
    print(result.outputs)

