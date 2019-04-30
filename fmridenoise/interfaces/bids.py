# Interface for loading preprocessed fMRI data and confounds table
# Modified code from poldracklab/fitlins/fitlins/interfaces/bids.py

import numpy as np
import os
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )
from nipype.interfaces.io import IOBase
from nipype.utils.filemanip import split_filename, copyfile

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


class BIDSDataSinkInputSpec(BaseInterfaceInputSpec):
    base_directory = Directory(
        mandatory=True,
        desc='Path to BIDS (or derivatives) root directory')
    in_file = InputMultiPath(File(exists=True), mandatory=True)
    suffix = traits.Str(mandatory=True)
    entities = InputMultiPath(traits.Dict, usedefault=True,
                              desc='Per-file entities to include in filename')


class BIDSDataSinkOutputSpec(TraitedSpec):
    out_file = OutputMultiPath(File, desc='output file')


class BIDSDataSink(IOBase):
    input_spec = BIDSDataSinkInputSpec
    output_spec = BIDSDataSinkOutputSpec

    _always_run = True

    def _list_outputs(self):
        base_dir = self.inputs.base_directory 
        os.makedirs(base_dir, exist_ok=True)
        
        out_files = []
        for entity, in_file in zip(self.inputs.entities, self.inputs.in_file):
            sub_num = entity['subject']
            basedir, basename, ext = split_filename(in_file)
            path = f"{base_dir}/derivatives/fmridenoise/sub-{sub_num}"
            os.makedirs(path, exist_ok=True)
            out_fname = f"{path}/{basename}_{self.inputs.suffix}{ext}" # TODO: Fix lonely dot if no extension
            copyfile(in_file, out_fname, copy=True)
            out_files.append(out_fname)
        return {'out_file': out_files}

# --- TESTS

if __name__ == '__main__':
    from nipype import Node
    # selector = Node(BIDSSelect(), name="pipeline_selector")
    # selector.inputs.bids_dir = '/home/finc/Dropbox/Projects/fitlins/BIDS/'
    # selector.inputs.derivatives = True
    # selector.inputs.entities = [{'subject': '01'}]
    # results = selector.run()
    # print(results.outputs)
    ds = Node(BIDSDataSink(base_directory='/home/siegfriedwagner/Documents/git/fmridenoise/dummy_bids', 
                            in_file='/home/siegfriedwagner/Documents/git/fmridenoise/dummy_bids/derivatives/sub-1/test',
                            entities=[{'subject': '1'}],
                            suffix='d'), name='ds')
    ds.run()
    #print(ds.result)

