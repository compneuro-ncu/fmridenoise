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
        extensions = ['Asym_preproc.nii.gz']

        for subject in np.sort(layout.get_subjects()):
            for session in np.sort(layout.get_sessions()):
                file = layout.get(subject=subject, session=session, task='rest', extensions=extensions)
                if file == []:
                    pass
                else:
                    entity = {'subject': subject, 'session': session}
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
    fmri_preprocessed = OutputMultiPath(File)
    confounds_raw = OutputMultiPath(File)
    entities = OutputMultiPath(traits.Dict)

class BIDSSelect(SimpleInterface):
    input_spec = BIDSSelectInputSpec
    output_spec = BIDSSelectOutputSpec

    def _run_interface(self, runtime):
        from bids.layout import BIDSLayout

        derivatives = self.inputs.derivatives
        layout = BIDSLayout(self.inputs.bids_dir, derivatives=derivatives)

        fmri_preprocessed = []
        confounds_raw = []
        entities = []

        for ents in self.inputs.entities:
            selectors = {**self.inputs.selectors, **ents}
            fmri_file = layout.get(extensions=['Asym_preproc.nii.gz'], **selectors)
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

            confounds = layout.get(extensions=['confounds.tsv'], **selectors)

            fmri_preprocessed.append(fmri_file[0].path)
            confounds_raw.append(confounds[0].path)

        self._results['fmri_preprocessed'] = fmri_preprocessed
        self._results['confounds_raw'] = confounds_raw
        self._results['entities'] = self.inputs.entities #entities

        return runtime
