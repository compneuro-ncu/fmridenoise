# Interface for loading preprocessed fMRI data and confounds table
# Modified code from poldracklab/fitlins/fitlins/interfaces/bids.py

import numpy as np

from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )


class BIDSLoadInputSpec(BaseInterfaceInputSpec):
    bids_dir = Directory(exists=True,
                         mandatory=True,
                         desc='BIDS dataset root directories')
    derivatives = traits.Either(True, InputMultiPath(Directory(exists=True)),
                                desc='Derivative folders')


class BIDSLoadOutputSpec(TraitedSpec):
    entities = OutputMultiPath(traits.Dict)


class BIDSLoad(SimpleInterface):
    input_spec = BIDSLoadInputSpec
    output_spec = BIDSLoadOutputSpec

    def _run_interface(self, runtime):
        from bids.layout import BIDSLayout

        layout = BIDSLayout(self.inputs.bids_dir, derivatives=True)

        entities = []
        extensions = ['preproc_bold.nii.gz']

        for subject in np.sort(layout.get_subjects()):
            file = layout.get(subject=subject, task=layout.get_tasks(), extensions=extensions)
            if file == []:
                pass
            else:
                entity = {'subject': subject}#, 'session': session}
                entities.append(entity)
                self._results['entities'] = entities

        return runtime


class BIDSSelectInputSpec(BaseInterfaceInputSpec):
    bids_dir = Directory(exists=True,
                         mandatory=True,
                         desc='BIDS dataset root directories')
    derivatives = traits.Either(True, InputMultiPath(Directory(exists=True)),
                                desc='Derivative folders')
    entities = InputMultiPath(traits.Dict(), mandatory=True)
    selectors = traits.Dict(desc='Additional selectors to be applied',
                            usedefault=True)


class BIDSSelectOutputSpec(TraitedSpec):
    fmri_prep = OutputMultiPath(File)
    conf_raw = OutputMultiPath(File)
    entities = OutputMultiPath(traits.Dict)


class BIDSSelect(SimpleInterface):
    input_spec = BIDSSelectInputSpec
    output_spec = BIDSSelectOutputSpec

    def _run_interface(self, runtime):
        from bids.layout import BIDSLayout

        derivatives = self.inputs.derivatives
        layout = BIDSLayout(self.inputs.bids_dir, derivatives=derivatives)

        fmri_prep = []
        conf_raw = []
        entities = []

        for ents in self.inputs.entities:
            selectors = {**self.inputs.selectors, **ents}
            fmri_file = layout.get(extensions=['preproc_bold.nii.gz'], **selectors)
            if len(fmri_file) == 0:
                raise FileNotFoundError(
                    "Could not find BOLD file in {} with entities {}"
                    "".format(self.inputs.bids_dir, selectors))
            elif len(fmri_file) > 1:
                raise ValueError(
                    "Non-unique BOLD file in {} with entities {}.\n"
                    "Matches:\n\t{}"
                    "".format(self.inputs.bids_dir, selectors,
                              "\n\t".join(
                                  '{} ({})'.format(
                                      f.path,
                                      layout.files[f.path].entities)
                                  for f in fmri_file)))

            confounds = layout.get(extensions=['confounds_regressors.tsv'], **selectors)

            fmri_prep.append(fmri_file[0].path)
            conf_raw.append(confounds[0].path)

        self._results['fmri_prep'] = fmri_prep
        self._results['conf_raw'] = conf_raw
        self._results['entities'] = self.inputs.entities #entities

        return runtime


# --- TESTS

if __name__ == '__main__':
    from nipype import Node
    selector = Node(BIDSSelect(), name="pipeline_selector")
    selector.inputs.bids_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/'
    selector.inputs.derivatives = True
    selector.inputs.entities = [{'subject': '01'}]
    results = selector.run()
    print(results.outputs)

