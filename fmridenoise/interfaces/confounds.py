from fmridenoise.utils import confound_prep
import pandas as pd
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, SimpleInterface, \
    InputMultiObject
from nipype.utils.filemanip import split_filename
from fmridenoise.utils.confound_prep import prep_conf_df


class ConfoundsInputSpec(BaseInterfaceInputSpec):
    pipeline = traits.Dict(
        desc="Denoising pipeline",
        mandatory=True)
    conf_raw = File(
        exist=True,
        desc="Confounds table",
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

class Confounds(SimpleInterface):
    input_spec = ConfoundsInputSpec
    output_spec = ConfoundsOutputSpec

    def _run_interface(self, runtime):

        fname = self.inputs.conf_raw
        conf_df_raw = pd.read_csv(fname, sep='\t')

        # Preprocess confound table according to pipeline
        conf_df_prep = prep_conf_df(conf_df_raw, self.inputs.pipeline)

        # Create new filename and save
        path, base, _ = split_filename(fname)  # Path can be removed later
        fname_prep = f"{self.inputs.output_dir}/{base}_prep.tsv"  # use output path
        conf_df_prep.to_csv(fname_prep, sep='\t', index=False)

        # Creates dictionary with summary measures
        n_spikes = conf_df_prep.filter(regex='spike', axis=1).sum().sum()
        mean_fd = conf_df_raw["framewise_displacement"].mean()
        max_fd = conf_df_raw["framewise_displacement"].max()
        n_timepoints = len(conf_df_raw)

        conf_summary = {
                        "subject": [self.inputs.entities['subject']],
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


class AggConfoundsInputSpec(BaseInterfaceInputSpec):
    conf_summary = traits.List(
        exists=True,
        desc="Confounds summary")

    output_dir = File(          # needed to save data in other directory
        desc="Output path")     # TODO: Implement temp dir


class AggConfoundsOutputSpec(TraitedSpec):
    group_conf_summary = File(
        exists=True,
        desc="Confounds summary")


class AggConfounds(SimpleInterface):
    input_spec = AggConfoundsInputSpec
    output_spec = AggConfoundsOutputSpec

    def _run_interface(self, runtime):
        group_conf_summary = pd.DataFrame()

        for summary in self.inputs.conf_summary:
            group_conf_summary = group_conf_summary.append(pd.DataFrame.from_dict(summary))

        fname = f"{self.inputs.output_dir}group_confounds_table.tsv"
        group_conf_summary.to_csv(fname, sep='\t', index=False)
        self._results['group_conf_summary'] = fname
        return runtime


# --- TESTS

# if __name__ == '__main__':
#     from nipype import Node
#     import utils as ut
#
#     prep_conf = Node(Confounds(), name="ConfPrep")
#
#     #jdicto = ut.load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
#     jdicto = ut.load_pipeline_from_json("../pipelines/pipeline-acomp_cor.json")
#     confpath = "/media/finc/Elements/BIDS_pseudowords/BIDS/derivatives/fmriprep/sub-01/func/" + \
#                "sub-01_task-rhymejudgment_desc-confounds_regressors.tsv"
#
#     cf = Confounds()
#     cf.inputs.pipeline = jdicto
#     cf.inputs.conf_raw = confpath
#     cf.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
#     results = cf.run()
#
#     print(results.outputs)

if __name__ == '__main__':
    from nipype import Node
    import utils as ut


    conf_summaries = [{'mean_fd': [0.11377746541635224], 'max_fd': [0.25027780000000005], 'n_spikes': [8], 'n_conf': [35], 'include_lib': [1], 'include_con': [1]},
                      {'mean_fd': [0.11377746541635224], 'max_fd': [0.25027780000000005], 'n_spikes': [8], 'n_conf': [35], 'include_lib': [1], 'include_con': [1]}]

    cf = AggConfounds()
    cf.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    cf.inputs.conf_summary = conf_summaries
    results = cf.run()
    print(results.outputs)
