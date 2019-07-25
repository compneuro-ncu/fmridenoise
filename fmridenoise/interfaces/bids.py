# Interface for loading preprocessed fMRI data and confounds table

from nipype.interfaces.io import IOBase
from nipype.utils.filemanip import split_filename, copyfile
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, SimpleInterface,
    traits, isdefined, TraitedSpec,
    Directory, File, Str, ImageFile,
    InputMultiObject, OutputMultiObject, OutputMultiPath, InputMultiPath)
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
        desc='Names of tasks to denoise'
    )

    session = InputMultiObject(
        Str,
        mandatory=False,
        desc='Names of sessions to denoise'
    )

    derivatives = traits.Either(
        traits.Str, traits.List(Str),
        default='fmriprep',
        usedefault=True,
        mandatory=False,
        desc='Specifies which derivatives to to index'
    )

    ica_aroma = traits.Bool(
        mandatory=False,
        desc='ICA-Aroma files'
    )



class BIDSGrabOutputSpec(TraitedSpec):
    fmri_prep = OutputMultiPath(ImageFile)
    fmri_prep_aroma = OutputMultiPath(ImageFile)
    conf_raw = OutputMultiPath(File)
    conf_json = OutputMultiPath(File)  # TODO: Kamil check
    entities = OutputMultiObject(traits.Dict)
    tr_dict = traits.Dict()


class BIDSGrab(SimpleInterface):
    """
    Read a BIDS dataset and grabs:
        (1) preprocessed imaging files,
        (2) confound regressor tables,
        (3) entities for corresponding files,
        (4) TR values for available tasks.

    Outputs
    -------

    fmri_prep : list of files
        List containing all paths to available preprocessed functional files.
        Files are searched using BIDSLayout.get() method with filters specifying
        extensions ".nii" or ".nii.gz", suffix "bold" and extension "prep"
        corresponding to preprocessed images.
    conf_raw: list of files
        List containing paths to confound regressors files. Elements of conf_raw
        list correspond to fmri_prep elements such that each regressor file is
        related to one imaging file.

    entities : list of dictionaries
        The entities list contains a list of entity dictionaries. Elements of
        entities list correspond to fmri_prep elements such that each entity
        describe one imaging files. Entities provide BIDS specific information
        about subject, session (if there is more than one), task and datatype.

    tr_dict: dictionary
        Contains information about TR setting for each requested task. If task
        are not specified, all tasks found are included.

    """
    input_spec = BIDSGrabInputSpec
    output_spec = BIDSGrabOutputSpec

    def _run_interface(self, runtime):

        import json
        from bids import BIDSLayout

        if isinstance(self.inputs.derivatives, str):
            self.inputs.derivatives = [self.inputs.derivatives]

        # Create full paths to derivatives folders
        derivatives = [os.path.join(self.inputs.bids_dir, 'derivatives', der)
                       for der in self.inputs.derivatives]

        ica_aroma = self.inputs.ica_aroma

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
                        f'task {t} is not found')  # TODO: find proper error to handle this
            task = self.inputs.task

        session = self.inputs.session  # TODO: To correct by Kamil

        # Define query filters
        keys_entities = ['subject', 'session', 'datatype', 'task']

        filter_fmri = {
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'preproc',
            'task': task,
            'session': session,
        }

        filter_fmri_aroma = {
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'smoothAROMAnonaggr',
            'task': task,
            'session': session,
        }

        filter_conf = {
            'extension': 'tsv',
            'suffix': 'regressors',
            'desc': 'confounds',
            'task': task,
            'session': session,
        }

        filter_conf_json = {
            'extension': 'json',
            'suffix': 'regressors',
            'desc': 'confounds',
            'task': task,
            'session': session,
        }

        # Grab files
        fmri_prep, fmri_prep_aroma, conf_raw, conf_json, entities = ([] for _ in range(5))

        for fmri_file in layout.get(scope=scope, **filter_fmri):

            entity_bold = fmri_file.get_entities()

            # Look for corresponding confounds file
            filter_entities = {key: value
                               for key, value in entity_bold.items()
                               if key in keys_entities}
            filter_conf.update(
                filter_entities)  # Add specific fields to constrain search

            filter_conf_json.update(
                filter_entities)  # Add specific fields to constrain search

            conf_file = layout.get(scope=scope, **filter_conf)
            conf_json_file = layout.get(scope=scope, **filter_conf_json)

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
                    )  # TODO: find proper warning (logging?)

                conf_file = conf_file[0]

            if not conf_json_file:
                raise FileNotFoundError(
                    f"Regressor file not found for file {fmri_file.path}"
                )
            else:
                # Add entity only if both files are available
                if len(conf_json_file) > 1:
                    print(
                          f"Warning: Multiple .json regressors found for file {fmri_file.path}.\n"
                          f"Selecting {conf_json_file[0].path}"
                    )
                # TODO: find proper warning (logging?)

                conf_json_file = conf_json_file[0]

            if ica_aroma:
                filter_fmri_aroma.update(filter_entities)  # Add specific fields to constrain search
                fmri_aroma_file = layout.get(scope=scope, **filter_fmri_aroma)

                if not fmri_aroma_file:
                    raise FileNotFoundError(
                        f"ICA-Aroma file not found for file {fmri_file.path}"
                    )

                else:
                    # Add entity only if both files are available
                    if len(fmri_aroma_file) > 1:
                        print(
                            f"Warning: Multiple ICA-Aroma files found for file {fmri_file.path}.\n"
                            f"Selecting {fmri_aroma_file[0].path}"
                        )
                    # TODO: find proper warning (logging?)

                    fmri_aroma_file = fmri_aroma_file[0]
                    fmri_prep_aroma.append(fmri_aroma_file.path)

            fmri_prep.append(fmri_file.path)
            conf_raw.append(conf_file.path)
            conf_json.append(conf_json_file.path)
            entities.append(filter_entities)


        # Extract TRs
        tr_dict = {}

        for t in task:
            filter_fmri_tr = filter_fmri.copy()
            filter_fmri_tr['task'] = t

            example_file = layout.get(**filter_fmri_tr)[0]
            tr = layout.get_metadata(example_file.path)['RepetitionTime']
            tr_dict[t] = tr

        self._results['fmri_prep'] = fmri_prep
        self._results['conf_raw'] = conf_raw
        self._results['conf_json'] = conf_json
        self._results['entities'] = entities
        self._results['tr_dict'] = tr_dict
        self._results['fmri_prep_aroma'] = fmri_prep_aroma

        return runtime


class BIDSDataSinkInputSpec(BaseInterfaceInputSpec):
    base_directory = Directory(
        mandatory=True,
        desc='Path to BIDS (or derivatives) root directory')
    in_file = InputMultiPath(File(exists=True), mandatory=True)
    pipeline_name = traits.Str(mandatory=True)
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
            sub_num = entity['subject']  # TODO: Add support for sessions
            session_num = entity['session'] # TODO: Add conditionals if no sessions
            basedir, basename, ext = split_filename(in_file)
            path = f"{base_dir}/derivatives/fmridenoise/sub-{sub_num}/ses-{session_num}"
            os.makedirs(path, exist_ok=True)
            out_fname = f"{path}/{basename}_pipeline-{self.inputs.pipeline_name}{ext}"
            copyfile(in_file, out_fname, copy=True)
            out_files.append(out_fname)
        return {'out_file': out_files}


# --- TESTS

if __name__ == '__main__':
    #path = '/media/finc/Elements/zmien_nazwe'
    #bids_dir = os.path.join(path, 'BIDS_2sub')
    bids_dir = '/media/finc/Elements/fMRIDenoise_data/BIDS_LearningBrain_short/'
    #bids_dir_2 = os.path.join(path, 'pilot_study_fmri_kids')
    #bids_dir_3 = os.path.join(path, 'test')

    #bids_dir = bids_dir_3
    task = ['rest']
    session = ['1']
    ica_aroma = True

    grabber = BIDSGrab(

        bids_dir=bids_dir,
        task=task,
        session=session,
        ica_aroma=ica_aroma
    )

    result = grabber.run()
    print(result.outputs)