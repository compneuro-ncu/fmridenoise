# Interface for loading preprocessed fMRI data and confounds table
from bids import BIDSLayout
from nipype.interfaces.io import IOBase
from nipype.utils.filemanip import split_filename, copyfile
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, SimpleInterface,
    traits, isdefined, TraitedSpec,
    Directory, File, Str, ImageFile,
    InputMultiObject, OutputMultiObject, OutputMultiPath, InputMultiPath)
import json
import os


def validate_derivatives(bids_dir, derivatives):
    """ Validate derivatives argument provided by the user.

    Args:
        bids_dir: list
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
            raise Exception(f"{derivative_path} should contain" +
                            " dataset_description.json file") from e
        except KeyError as e:
            raise Exception(f"Key 'PipelineDescription.Name' is " +
                            "required in {dataset_desc_path} file") from e

    return derivatives_valid, scope


def validate_option(layout, option, kind='task'):
    """ Validate BIDS query filters provided by the user.

    Args:
        layout: bids.layout.layout.BIDSLayout
            Lightweight class representing BIDS project file tree.
        option: list
            Filter arguments provided by the user.
        kind: string
            Type of query. Available options are 'task', 'session' and
            'subject'.

    Returns:
        option_: list
            Validated filter values.
    """
    # Grab all possible filter values

    if kind == 'task':
        option_all = layout.get_tasks()
    elif kind == 'session':
        option_all = layout.get_sessions()
    elif kind == 'subject':
        option_all = layout.get_subjects()
    else:
        raise ValueError("kind should be either 'task', 'session' or 'subject'")

    option_ = option
    for option_item in option_:
        if option_item not in option_all:
            raise ValueError(f'{kind} {option_item} is not found')

    return option_


def compare_common_entities(file1, file2) -> None:
    """Compare common entities for two layout files"""

    common_keys = ['task', 'session', 'subject', 'datatype']
    entity_f1 = {key: value for key, value in file1.get_entities().items() if
                 key in common_keys}
    entity_f2 = {key: value for key, value in file2.get_entities().items() if
                 key in common_keys}

    if not entity_f1 == entity_f2:
        raise MissingFile(f"{file1.path} has no corresponding file. "
                          f"Entities {entity_f1} and {entity_f2} should match.")


class MissingFile(IOError):
    pass


class BIDSGrabInputSpec(BaseInterfaceInputSpec):
    bids_dir = Directory(
        exists=True,
        mandatory=True,
        desc='BIDS dataset root directory'
    )
    derivatives = traits.Either(
        traits.Str, traits.List(Str),
        default='fmriprep',
        usedefault=True,
        mandatory=False,
        desc='Specifies which derivatives to to index')
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
    subject = InputMultiObject(
        Str,
        mandatory=False,
        desc='Labels of subjects to denoise'
    )
    ica_aroma = traits.Bool(
        mandatory=False,
        desc='ICA-Aroma files'
    )


class BIDSGrabOutputSpec(TraitedSpec):
    fmri_prep = OutputMultiPath(ImageFile)
    fmri_prep_aroma = OutputMultiPath(ImageFile)
    conf_raw = OutputMultiPath(File)
    conf_json = OutputMultiPath(File)
    entities = OutputMultiObject(traits.Dict)
    tr_dict = traits.Dict()


class BIDSGrab(SimpleInterface):  # TODO: update documentation
    """
    Read a BIDS dataset and grabs:
        (1) preprocessed imaging files,
        (2) confound regressor tables,
        (3) entities for corresponding files,
        (4) TR values for available tasks.

    Returns:
        fmri_prep: list of files
            List containing all paths to available preprocessed functional files.
            Files are searched using BIDSLayout.get() method with filters specifying
            extensions ".nii" or ".nii.gz", suffix "bold" and extension "prep"
            corresponding to preprocessed images.

        fmri_prep_aroma: ...

        conf_raw: list of files
            List containing paths to confound regressors files. Elements of conf_raw
            list correspond to fmri_prep elements such that each regressor file is
            related to one imaging file.

        conf_json: ...

        entities: list of dictionaries
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

        # Validate derivatives argument
        derivatives, scope = validate_derivatives(
            bids_dir=self.inputs.bids_dir,
            derivatives=self.inputs.derivatives
        )

        layout = BIDSLayout(
            root=self.inputs.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=False
        )
        print(*layout.get(), sep='\n')

        # Validate optional arguments
        filter_base = {}
        if isdefined(self.inputs.task):
            task = validate_option(layout, self.inputs.task, kind='task')
            filter_base['task'] = task
        else:
            task = layout.get_tasks()
        if isdefined(self.inputs.session):
            session = validate_option(layout, self.inputs.session,
                                      kind='session')
            filter_base['session'] = session
        if isdefined(self.inputs.subject):
            subject = validate_option(layout, self.inputs.subject,
                                      kind='subject')
            filter_base['subject'] = subject

        # Define query filters
        filter_fmri = {
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'preproc'
        }
        filter_fmri_aroma = {
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'smoothAROMAnonaggr',
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
        filter_fmri.update(filter_base)
        filter_fmri_aroma.update(filter_base)
        filter_conf.update(filter_base)
        filter_conf_json.update(filter_base)

        # Grab all requested files
        fmri_prep = layout.get(scope=scope, **filter_fmri)
        if self.inputs.ica_aroma:
            fmri_prep_aroma = layout.get(scope=scope, **filter_fmri_aroma)
        conf_raw = layout.get(scope=scope, **filter_conf)
        conf_json = layout.get(scope=scope, **filter_conf_json)

        # Validate correspondence between queried files
        entities = []
        for i, fmri_file in enumerate(fmri_prep):

            # reference common entities for preprocessed files
            if self.inputs.ica_aroma:
                compare_common_entities(fmri_file, fmri_prep_aroma[i])
            compare_common_entities(fmri_file, conf_raw[i])
            compare_common_entities(fmri_file, conf_json[i])

            entities.append({key: value for key, value in
                             fmri_file.get_entities().items()
                             if key in ['task', 'session', 'subject', 'datatype']})

        # Extract TRs
        tr_dict = {}

        #TODO: this is just a funny workaround, look for better solution later
        layout_for_tr = BIDSLayout(
            root=self.inputs.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=True
        )

        for t in task:
            filter_fmri_tr = filter_fmri.copy()
            filter_fmri_tr['task'] = t

            try:
                example_file = layout_for_tr.get(**filter_fmri_tr)[0]
            except IndexError:
                raise MissingFile(f"no imaging file found for task {t}")
            tr_dict[t] = layout_for_tr.get_metadata(example_file.path)['RepetitionTime']

        self._results['fmri_prep'] = [file.path for file in fmri_prep]
        if self.inputs.ica_aroma:
            self._results['fmri_prep_aroma'] = [file.path for file in fmri_prep_aroma]
        self._results['conf_raw'] = [file.path for file in conf_raw]
        self._results['conf_json'] = [file.path for file in conf_json]
        self._results['entities'] = entities
        self._results['tr_dict'] = tr_dict

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
            sub_num = entity['subject']
            basedir, basename, ext = split_filename(in_file)
            sub_deriv_dir = f"/derivatives/fmridenoise/sub-{sub_num}/"

            try:
                session_num = entity['session']
                path = f"{base_dir}{sub_deriv_dir}ses-{session_num}"
            except KeyError:
                path = f"{base_dir}/{sub_deriv_dir}"

            os.makedirs(path, exist_ok=True)
            out_fname = f"{path}/{basename}{ext}"
            copyfile(in_file, out_fname, copy=True)
            out_files.append(out_fname)
        return {'out_file': out_files}


# --- TESTS
if __name__ == '__main__':

    bids_dir = "./../../tests/interfaces/bids_grab/ds000003-00001_dummy"

    grabber = BIDSGrab(bids_dir=bids_dir)
    result = grabber.run()

    print(result.outputs)