from fmridenoise.utils import confound_prep
import pandas as pd
import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec, SimpleInterface
from nipype.utils.filemanip import split_filename
from fmridenoise.utils.confound_prep import prep_conf_df


class ConfoundsInputSpec(BaseInterfaceInputSpec):
    pipeline = traits.Dict(
        desc='Denoising pipeline',
        mandatory=True)
    conf_raw = File(
        exist=True,
        desc='Confounds table',
        mandatory=True)
    output_dir = File(          # needed to save data in other directory
        desc='Output path')     # TODO: Implement temp dir


class ConfoundsOutputSpec(TraitedSpec):
    conf_prep = File(
        exists=True,
        desc="Preprocessed confounds table")


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
        fname_prep = f"{self.inputs.output_dir}/{base}_{self.inputs.pipeline['name']}_prep.tsv"  # use output path
        conf_df_prep.to_csv(fname_prep, sep='\t', index=False)
        self._results['conf_prep'] = fname_prep

        return runtime



# --- TESTS

if __name__ == '__main__':
    from nipype import Node
    import utils as ut

    prep_conf = Node(Confounds(), name="ConfPrep")

    jdicto = ut.load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    confpath = "/home/finc/Dropbox/Projects/fitlins/BIDS/derivatives/fmriprep/sub-09/func/" + \
               "sub-09_task-rhymejudgment_desc-confounds_regressors.tsv"

    cf = Confounds()
    cf.inputs.pipeline = jdicto
    cf.inputs.conf_raw = confpath
    cf.inputs.output_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/derivatives/fmridenoise'
    results = cf.run()

    print(results.outputs)