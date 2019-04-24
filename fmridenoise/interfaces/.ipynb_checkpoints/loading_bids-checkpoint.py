# Interface for loading preprocessed fMRI data and confounds table
# Modified code from poldracklab/fitlins/fitlins/interfaces/bids.py

from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )


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
    bold_files = OutputMultiPath(File)
    confounds_files = OutputMultiPath(File)
    entities = OutputMultiPath(traits.Dict)
    
class BIDSSelect(SimpleInterface):
    input_spec = BIDSSelectInputSpec
    output_spec = BIDSSelectOutputSpec
    
    def _run_interface(self, runtime):
        from bids.layout import BIDSLayout

        derivatives = self.inputs.derivatives
        layout = BIDSLayout(self.inputs.bids_dir, derivatives=derivatives)

        bold_files = []
        confounds_files = []
        entities = []
        
        for ents in self.inputs.entities:
            selectors = {**self.inputs.selectors, **ents}
            bold_file = layout.get(extensions=['Asym_preproc.nii.gz'], **selectors)
            if len(bold_file) == 0:
                raise FileNotFoundError(
                    "Could not find BOLD file in {} with entities {}"
                    "".format(self.inputs.bids_dir, selectors))
            elif len(bold_file) > 1:
                raise ValueError(
                    "Non-unique BOLD file in {} with entities {}.\n"
                    "Matches:\n\t{}"
                    "".format(self.inputs.bids_dir, selectors,
                              "\n\t".join(
                                  '{} ({})'.format(
                                      f.path,
                                      layout.files[f.path].entities)
                                  for f in bold_file)))
                
            confounds_file = layout.get(extensions=['confounds.tsv'], **selectors)

            bold_files.append(bold_file[0].path)
            confounds_files.append(confounds_file[0].path)
        
        self._results['bold_files'] = bold_files
        self._results['confounds_files'] = confounds_files
        self._results['entities'] = self.inputs.entities #entities

        return runtime