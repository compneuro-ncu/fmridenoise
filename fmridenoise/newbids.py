from bids import BIDSLayout
from nipype.interfaces.base import BaseInterfaceInputSpec, SimpleInterface
from nipype.interfaces.base import traits, isdefined, \
    TraitedSpec, \
    Directory, File, Str, ImageFile, \
    InputMultiObject, OutputMultiObject, OutputMultiPath, InputMultiPath
import os

class BIDSGrabInputSpec(BaseInterfaceInputSpec):
    bids_dir = Directory(
        exists=True,
        mandatory=True,
        desc='BIDS dataset root directory'
    )
    task = InputMultiObject(
        Str,
        mandatory=False,
        desc='names of tasks to denoise'
    )
    derivatives = traits.Either(
        traits.Str, traits.List(Str),
        default='fmriprep',
        usedefault=True,
        mandatory=False,
        desc='Specifies which derivatives to to index'
    )

class BIDSGrabOutputSpec(TraitedSpec):
    fmri_prep = OutputMultiPath(ImageFile)
    conf_raw = OutputMultiPath(File)
    entities = OutputMultiObject(traits.Dict)

class BIDSGrab(SimpleInterface):
    input_spec = BIDSGrabInputSpec
    output_spec = BIDSGrabOutputSpec

    def _run_interface(self, runtime):

        import json

        if isinstance(self.inputs.derivatives, str):
            self.inputs.derivatives = [self.inputs.derivatives]

        # Create full paths to derivatives folders
        derivatives = [os.path.join(self.inputs.bids_dir, 'derivatives', der)
                       for der in self.inputs.derivatives]

        # Establish right scope keyword for arbitrary packages
        scope = []
        for derivative_path in derivatives:
            dataset_desc_path = os.path.join(derivative_path,
                                             'dataset_description.json')
            try:
                with open(dataset_desc_path, 'r') as f:
                    dataset_desc = json.load(f)
                scope.append(dataset_desc['PipelineDescription']['Name'])
            except FileNotFoundError as e:
                raise Exception(f"{derivative_path} should contain" +
                    " dataset_description.json file") from e
            except KeyError as e:
                raise Exception(f"Key 'PipelineDescription.Name' is " +
                    "required in {dataset_desc_path} file") from e

        layout = BIDSLayout(
            root=self.inputs.bids_dir,
            validate=True,
            derivatives=derivatives
        )

        # Tasks to denoise
        if not isdefined(self.inputs.task):
            task = layout.get_tasks()  # Grab all available tasks
        else:
            for t in self.inputs.task:
                if t not in layout.get_tasks():
                    raise ValueError(
                        f'task {t} is not found')                               # TODO: find proper error to handle this
            task = self.inputs.task

        # Define query filters
        keys_entities = ['subject', 'session', 'datatype', 'task']
        filter_fmri = {
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'preproc',
            'task': task
        }
        filter_conf = {
            'extension': 'tsv',
            'suffix': 'regressors',
            'desc': 'confounds'
        }

        # Grab files
        fmri_prep, conf_raw, entities = ([] for _ in range(3))

        for fmri_file in layout.get(scope=scope, **filter_fmri):

            entity_bold = fmri_file.get_entities()

            # Look for corresponding confounds file
            filter_entities = {key: value
                               for key, value in entity_bold.items()
                               if key in keys_entities}
            filter_conf.update(
                filter_entities)  # Add specific fields to constrain search
            conf_file = layout.get(scope=scope, **filter_conf)

            if not conf_file:
                raise FileNotFoundError(
                    f"Regressor file not found for file {fmri_file.path}"
                )
            else:
                # Add entity only if both files are available
                if len(conf_file) > 1:
                    print(
                        f"Warning: Multiple regressors found for file {fmri_file.path}.\n"
                        f"Selecting {conf_file[0].path}"
                    )                                                           # TODO: find proper warning (logging?)

                conf_file = conf_file[0]

                fmri_prep.append(fmri_file.path)
                conf_raw.append(conf_file.path)
                entities.append(filter_entities)

        self._results['fmri_prep'] = fmri_prep
        self._results['conf_raw'] = conf_raw
        self._results['entities'] = entities

        return runtime


#=== Testing
if __name__ == "__main__":

    path = '/home/kmb/Desktop/Neuroscience/Projects/NBRAINGROUP_fmridenoise/test_data'
    bids_dir_1 = os.path.join(path, 'BIDS_2sub')
    bids_dir_2 = os.path.join(path, 'synthetic')
    bids_dir_3 = os.path.join(path, 'pilot_study_fmri_kids')

    bids_dir = bids_dir_3
    task = []

    grabber = BIDSGrab(
        bids_dir=bids_dir,
        task=task
    )

    result = grabber.run()
    print(result.outputs)

