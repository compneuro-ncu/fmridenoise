from fmridenoise.utils import confound_prep
import pandas as pd
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, SimpleInterface
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
        conf_summary = {"mean_fd": [conf_df_raw["framewise_displacement"].mean()],
                        "max_fd": [conf_df_raw["framewise_displacement"].max()],
                        "n_spikes": [conf_df_prep.filter(regex='spike', axis=1).sum().sum()],
                        "n_conf": [len(conf_df_prep.columns)]}

        self._results['conf_prep'] = fname_prep
        self._results['conf_summary'] = conf_summary

        return runtime



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
#     conf_summaries = [{'max_fd': [0.25027780000000005], 'mean_fd': [0.11377746541635224], 'n_conf': [35], 'n_spikes': [8]}, {'max_fd': [0.3917644499999999], 'mean_fd': [0.14487157071698104], 'n_conf': [58], 'n_spikes': [31]}]
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


    conf_summaries = [{'max_fd': [0.25027780000000005], 'mean_fd': [0.11377746541635224], 'n_conf': [35], 'n_spikes': [8]}, {'max_fd': [0.3917644499999999], 'mean_fd': [0.14487157071698104], 'n_conf': [58], 'n_spikes': [31]}]

    cf = AggConfounds()
    cf.inputs.output_dir = '/media/finc/Elements/fmridenoise/derivatives/fmridenoise/'
    cf.inputs.conf_summary = conf_summaries
    results = cf.run()
    print(results.outputs)
