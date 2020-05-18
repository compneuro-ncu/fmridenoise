# Interface for loading preprocessed fMRI data and confounds table
from bids import BIDSLayout
from nipype.interfaces.io import IOBase
from nipype.utils.filemanip import split_filename, copyfile
from nipype.interfaces.base import (BaseInterfaceInputSpec, SimpleInterface,
    traits, TraitedSpec,
    Directory, Str, ImageFile,
    OutputMultiPath)
from traits.trait_types import Dict, List, Either, File
from fmridenoise.pipelines import load_pipeline_from_json, is_IcaAROMA
import json
import os
from itertools import product
from os.path import join
import typing as t


class MissingFile(IOError):
    pass


class BIDSGrabInputSpec(BaseInterfaceInputSpec):

    fmri_prep_files = List()
    fmri_prep_aroma_files = Either(List(ImageFile()), File())
    conf_raw_files = Either(List(File(exists=True)), File())
    conf_json_files = Either(List(File(exists=True)), File())
    subject = Str()
    task = Str()
    session = Str()


class BIDSGrabOutputSpec(TraitedSpec):
    fmri_prep = ImageFile()
    fmri_prep_aroma = ImageFile()
    conf_raw = File(exists=True)
    conf_json = File(exists=True)


class BIDSGrab(SimpleInterface):
    input_spec = BIDSGrabInputSpec
    output_spec = BIDSGrabOutputSpec

    def _run_interface(self, runtime):
        self._results['fmri_prep'] = self.select_one(self.inputs.fmri_prep_files)
        self._results['fmri_prep_aroma'] = self.select_one(self.inputs.fmri_prep_aroma_files)
        self._results['conf_raw'] = self.select_one(self.inputs.conf_raw_files)
        self._results['conf_json'] = self.select_one(self.inputs.conf_json_files)
        return runtime

    def select_one(self, _list: t.List[str]) -> str:
        """
        Wraper for _select_one that uses class instance variable.
        Args:
            _list (List[str]): list of file paths
        Returns:
           str: resulting file path meeting criteria
        """
        return self._select_one(_list,
                                self.inputs.subject,
                                self.inputs.session,
                                self.inputs.task)

    @staticmethod
    def _select_one(_list: t.List[str], subject: str, session: str, task: str) -> str:
        """
        For given list of file paths returns one path for given subject, session and task.
        If no paths meet criteria empty string is returned instead.
        If more than one path is found ValueError is raised.
        Args:
            _list (List[str]): list of file paths
            subject (str): subject identifier without 'sub-'
            session (str): session identifier without 'ses-'
            task (str): task identifier without 'task-'

        Returns:
           str: resulting file path meeting criteria
        """
        if session:
            query = lambda data_list: list(
                filter(lambda x: f"sub-{subject}" in x,
                filter(lambda x: f"ses-{session}" in x,
                filter(lambda x: f"task-{task}" in x, data_list))))
        else:
            query = lambda data_list: list(
                filter(lambda x: f"sub-{subject}" in x,
                filter(lambda x: f"task-{task}" in x, data_list)))
        result = query(_list)
        if not len(result) <= 1:
            raise ValueError(f"Unambiguous number of querried files, expected 1 or 0 but got {len(result)}")
        return result[0] if len(result) == 1 else ''


class BIDSValidateInputSpec(BaseInterfaceInputSpec):

    # Root directory only required argument
    bids_dir = Directory(
        exists=True,
        required=True,
        desc='BIDS dataset root directory'
    )

    # Default: 'fmriprep'
    derivatives = traits.List(desc='Specifies name of derivatives directory')

    # Separate queries from user
    tasks = traits.List(Str, desc='Names of tasks to denoise')
    sessions = traits.List(Str, desc='Labels of sessions to denoise')
    subjects = traits.List(Str, desc='Labels of subjects to denoise')

    # Pipelines from user or default
    pipelines = traits.List(
        File,
        desc='List of paths to selected pipelines'
    )


class BIDSValidateOutputSpec(TraitedSpec):

    # Goes to BIDSGrab (whole lists)
    fmri_prep = traits.List(File)
    fmri_prep_aroma = traits.List(File)
    conf_raw = traits.List(File)
    conf_json = traits.List(File)

    # Goes to BIDSGrab (one-by-one)
    tasks = traits.List(Str)
    sessions = traits.List(Str)
    subjects = traits.List(Str)

    # Outputs pipelines loaded as dicts
    pipelines = traits.List(Dict)

    # Goes to Denoiser
    tr_dict = traits.Dict()


class BIDSValidate(SimpleInterface):
    '''
    Interface responsible for calling BIDSLayout and validating file structure.

    It should output to:
    - layout (-> BIDSGrab)
    - task, session, subject  (-> iterNodes)
    - pipeline (-> ?)
    - tr_dict (-> Denoiser)

    It should raise exception when:
    - user specified incorrect flags (there are no matching files)
    - some files are missing e.g. these for AROMA pipeline, when it is required

    '''
    input_spec = BIDSValidateInputSpec
    output_spec = BIDSValidateOutputSpec

    @staticmethod
    def validate_derivatives(bids_dir: str,
                             derivatives: t.Union[str, t.List[str]]) -> t.Tuple[t.List[str], t.List[str]]:
        """ Validate derivatives argument provided by the user before calling
        layout. It creates required full path for derivatives directory. Also
        returns scope required for queries.

        Args:
            bids_dir: str
                Path to bids root directory.
            derivatives: str or list(str)
                Derivatives to use for denoising.

        Returns:
            derivatives_valid: list
                Validated derivatives list.
            scope: list
                Right scope keyword used in pybids query.
        """

        if isinstance(derivatives, str):
            derivatives_valid = [derivatives]
        else:
            derivatives_valid = derivatives

        # Create full paths to derivatives folders
        derivatives_valid = [os.path.join(bids_dir, 'derivatives', d)
                             for d in derivatives_valid]

        # Establish right scope keyword for arbitrary packages
        scope = []
        for derivative_path in derivatives_valid:
            dataset_desc_path = os.path.join(derivative_path,
                                             'dataset_description.json')
            try:
                with open(dataset_desc_path, 'r') as f:
                    dataset_desc = json.load(f)
                scope.append(dataset_desc['PipelineDescription']['Name'])
            except FileNotFoundError as e:
                raise MissingFile(f"{derivative_path} should contain" +
                                " dataset_description.json file") from e
            except KeyError as e:
                raise MissingFile(f"Key 'PipelineDescription.Name' is " +
                                "required in {dataset_desc_path} file") from e

        return derivatives_valid, scope

    @staticmethod
    def validate_files(layout, tasks, sessions, subjects, include_aroma, include_no_aroma):
        '''...'''

        def fill_empty_lists(subjects: list, tasks: list, sessions: list):
            '''If filters are not provided by the user, load them from layout.'''

            if not subjects:    subjects = layout.get_subjects()
            if not tasks:       tasks = layout.get_tasks()
            if not sessions:    sessions = layout.get_sessions()

            return subjects, tasks, sessions

        def lists_to_entities(subjects: list, tasks: list, sessions: list):
            '''Convert lists of subjects, tasks and sessions into list of dictionaries
            (entities). It handles empty session list.'''

            keys = ('subject', 'task', 'session')
            entities = []

            if not sessions:
                entities_list = product(subjects, tasks)
            else:
                entities_list = product(subjects, tasks, sessions)

            for entity in entities_list:
                entities.append(
                    {key: value for key, value in zip(keys, entity)})

            return entities

        def get_entity_files(include_no_aroma: bool, include_aroma: bool, entity: dict) -> tuple:
            '''Checks if all required files are present for single entity defined by
            subject, session and task labels. If include_aroma is True also checks for
            AROMA file. Note that session argument can be undefined.

            Args:

            Returns:
                (missing: bool, dict)

            '''
            filter_fmri = {
                'extension': ['nii', 'nii.gz'],
                'suffix': 'bold',
                'desc': 'preproc',
                'space': 'MNI152NLin2009cAsym'
            }
            filter_fmri_aroma = {
                'extension': ['nii', 'nii.gz'],
                'suffix': 'bold',
                'desc': 'smoothAROMAnonaggr',
                # 'space': 'MNI152NLin2009cAsym'
            }
            filter_conf = {
                'extension': 'tsv',
                'suffix': 'regressors',
                'desc': 'confounds',
            }
            filter_conf_json = {
                'extension': 'json',
                'suffix': 'regressors',
                'desc': 'confounds',
            }

            filters_names = ['conf_raw', 'conf_json']
            filters = [filter_fmri, filter_conf, filter_conf_json]
            if include_no_aroma:
                filters.append(filter_fmri)
                filters_names.append('fmri_prep')
            if include_aroma:
                filters.append(filter_fmri_aroma)
                filters_names.append('fmri_prep_aroma')

            entity_files = {}

            for filter, filter_name in zip(filters, filters_names):
                files = layout.get(**entity, **filter)
                if len(files) != 1:
                    return True, None
                entity_files[filter_name] = files[0]

            return False, entity_files

        # Select interface behavior depending on user behavior
        if not tasks and not sessions and not subjects:
            raise_missing = False
            subjects_to_exclude = []
        else:
            raise_missing = True

        subjects, tasks, sessions = fill_empty_lists(subjects, tasks, sessions)
        entities = lists_to_entities(subjects, tasks, sessions)
        entities_files = []

        if raise_missing:
            # Raise error if there are missing files
            for entity in entities:

                missing, entity_files = get_entity_files(include_no_aroma, include_aroma, entity)
                entities_files.append(entity_files)

                if missing:
                    raise MissingFile(
                        f'missing file(s) for {entity} (check if you are using AROMA pipelines)')
        else:
            # Log missing files and exclude subjects for missing files
            for entity in entities:

                missing, entity_files = get_entity_files(include_no_aroma, include_aroma, entity)
                entities_files.append(entity_files)

                if missing:
                    subjects_to_exclude.append(entity['subject'])
                    print(f'missing file(s) for {entity}')  # TODO: proper logging

            subjects = [subject for subject in subjects if
                        subject not in subjects_to_exclude]

        return entities_files, (tasks, sessions, subjects)

    def _run_interface(self, runtime):

        # Validate derivatives argument
        derivatives, scope = BIDSValidate.validate_derivatives(
            bids_dir=self.inputs.bids_dir,
            derivatives=self.inputs.derivatives
        )

        # Load layout
        layout = BIDSLayout(
            root=self.inputs.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=False
        )

        # Load pipelines
        pipelines_dicts = []
        for pipeline in self.inputs.pipelines:
            pipelines_dicts.append(load_pipeline_from_json(pipeline))

        # Check if there is at least one pipeline requiring aroma
        include_aroma = any(map(is_IcaAROMA, pipelines_dicts))

        # Check if there is at least one pipeline requiring no armoa files
        include_no_aroma = not all(map(is_IcaAROMA, pipelines_dicts))

        # Check missing files and act accordingly
        entities_files, (tasks, sessions, subjects) = BIDSValidate.validate_files(
            layout=layout,
            tasks=self.inputs.tasks,
            sessions=self.inputs.sessions,
            subjects=self.inputs.subjects,
            include_aroma=include_aroma,
            include_no_aroma=include_no_aroma
        )

        # Convert entities_files into separate lists of BIDSImageFile Objects
        conf_raw = list(map(lambda d: d['conf_raw'].path, entities_files))
        conf_json = list(map(lambda d: d['conf_json'].path, entities_files))

        if include_no_aroma:
            fmri_prep = list(map(lambda d: d['fmri_prep'].path, entities_files))
        else:
            fmri_prep = []

        if include_aroma:
            fmri_prep_aroma = list(map(lambda d: d['fmri_prep_aroma'].path, entities_files))
        else:
            fmri_prep_aroma = []

        # Extract TR for specific tasks
        tr_dict = {}

        # TODO: this is just a funny workaround, look for better solution later
        layout_for_tr = BIDSLayout(
            root=self.inputs.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=True
        )

        for task in tasks:
            filter_fmri_tr = {
                'extension': ['nii', 'nii.gz'],
                'suffix': 'bold',
                'desc': 'preproc',
                'space': 'MNI152NLin2009cAsym',
                'task': task
            }

            try:
                example_file = layout_for_tr.get(**filter_fmri_tr)[0]
            except IndexError:
                raise MissingFile(f'no imaging file found for task {task}')
            tr_dict[task] = layout_for_tr.get_metadata(example_file.path)[
                'RepetitionTime']

        # Prepare outputs
        self._results['fmri_prep'] = fmri_prep
        self._results['fmri_prep_aroma'] = fmri_prep_aroma
        self._results['conf_raw'] = conf_raw
        self._results['conf_json'] = conf_json
        self._results['tasks'] = tasks
        self._results['sessions'] = sessions
        self._results['subjects'] = subjects
        self._results['pipelines'] = pipelines_dicts
        self._results['tr_dict'] = tr_dict

        return runtime


class BIDSDataSinkInputSpec(BaseInterfaceInputSpec):
    base_directory = Directory(
        mandatory=True,
        desc='Path to BIDS (or derivatives) root directory')
    in_file = File(
        exists=True,
        mandatory=True,
        desc="File from tmp to save in BIDS directory")
    subject = Str(
        mandatory=False,
        desc="Subject name")
    session = Str(
        mandatory=False,
        desc="Session name")


class BIDSDataSinkOutputSpec(TraitedSpec):
    out_file = OutputMultiPath(File, desc='output file')


class BIDSDataSink(IOBase):
    """
    Copies files created by workflow to bids-like folder.
    """
    input_spec = BIDSDataSinkInputSpec
    output_spec = BIDSDataSinkOutputSpec

    _always_run = True

    def _list_outputs(self):
        path = join(self.inputs.base_directory, "derivatives", "fmridenoise")
        if self.inputs.subject:
            path = join(path, f"sub-{self.inputs.subject}")
        if self.inputs.session:
            path = join(path, f"ses-{self.inputs.session}")
        os.makedirs(path, exist_ok=True)
        basedir, basename, ext = split_filename(self.inputs.in_file)
        path = join(path, basename+ext)
        assert not os.path.exists(path), f"Path {path} already exists."
        copyfile(self.inputs.in_file, path, copy=True)
        return {'out_file': path}
