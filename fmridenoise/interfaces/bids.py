# Interface for loading preprocessed fMRI data and confounds table
from bids import BIDSLayout
from nipype.interfaces.io import IOBase
from nipype.utils.filemanip import split_filename, copyfile
from nipype.interfaces.base import (BaseInterfaceInputSpec, SimpleInterface,
    traits, isdefined, TraitedSpec,
    Directory, File, Str, ImageFile,
    InputMultiObject, OutputMultiObject, OutputMultiPath, InputMultiPath)
from traits.trait_types import Any, Dict, List
import json
import os
import re


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

def create_template(path: str, 
                    patterns: dict = 
                    {'sub-{sub_id}': 'sub-\d{1,}',
                    'ses-{ses_id}': 'ses-\d{1,}',
                    'task-{task_id}': 'task-[^_/.]*'}) -> str:
    for replacement, pattern in patterns.items():
        path, number = re.subn(pattern, replacement, path)
    return path

class MissingFile(IOError):
    pass


class BIDSGrabInputSpec(BaseInterfaceInputSpec):
    layout = Any(required=True) # todo strict type checking
    scope = List(Str(), required=True)
    tr_dict = Dict(required=True)
    subject = Str()
    task = Str()
    session = Str()



class BIDSGrabOutputSpec(TraitedSpec):
    fmri_prep = ImageFile()
    fmri_prep_aroma = ImageFile()
    conf_raw = File(exists=True)
    conf_json = File(exists=True)
    entity = Dict()

class BIDSGrab(SimpleInterface):
    input_spec = BIDSGrabInputSpec
    output_spec = BIDSGrabOutputSpec

    def _run_interface(self, runtime):
        fmri_prep = self.inputs.layout.get(
            scope=self.inputs.scope,
            **{
            'subject': self.inputs.subject,
            'session': self.inputs.session,
            'task': self.inputs.task,
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'smoothAROMAnonaggr',
            'space': 'MNI152NLin2009cAsym'
            })
        fmri_aroma = self.inputs.layout.get(
            scope=self.inputs.scope,
            **{
            'subject': self.inputs.subject,
            'session': self.inputs.session,
            'task': self.inputs.task,
            'extension': ['nii', 'nii.gz'],
            'suffix': 'bold',
            'desc': 'smoothAROMAnonaggr',
            'space': 'MNI152NLin2009cAsym'
        })
        conf = self.layout.get(
            scope=self.inputs.scope,
            **{
            'subject': self.inputs.subject,
            'session': self.inputs.session,
            'task': self.inputs.task,
            'extension': 'tsv',
            'suffix': 'regressors',
            'desc': 'confounds',
        })
        conf_json = self.layout.get(
            scope=self.inputs.scope,
            **{
            'subject': self.inputs.subject,
            'session': self.inputs.session,
            'task': self.inputs.task,
            'extension': 'json',
            'suffix': 'regressors',
            'desc': 'confounds',
        })
        # sanity check
        if len(fmri_prep) > 1:
            raise ValueError(f"Expected single or none fmri_prep file, but got: {fmri_prep}")
        if len(fmri_aroma) > 1:
            raise ValueError(f"Expected single or none fmri_prep aroma file, but got: {fmri_aroma}")
        if len(conf) != 1:
            raise ValueError(f"Expected single confounds file, but got: {conf}")
        if len(conf_json) != 1:
            raise ValueError(f"Expected single confounds_json file, but got: {conf_json}")
        
        self._results.fmri_prep = fmri_prep[0].path
        self._results.fmri_aroma = fmri_aroma[0].path
        self._results.conf_raw = conf[0].path
        self._results.conf_json = conf_json[0].path
        self._results


class BIDSSelect(traits.HasRequiredTraits):
    bids_dir = Directory(
        exists=True,
        required=True,
        desc='BIDS dataset root directory'
    )
    derivatives = traits.List(
        desc='Specifies which derivatives to to index'
    )
    task = traits.List(
        Str,
        desc='Names of tasks to denoise'
    )
    session = traits.List(
        Str,
        desc='Names of sessions to denoise'
    )
    subject = traits.List(
        Str,
        desc='Labels of subjects to denoise'
    )
    ica_aroma = traits.Bool(
        desc='ICA-Aroma files'
    )
    _templates = traits.DictStrStr()
    _layout = traits.Any()
    _tr_dict = traits.Dict()
    scope = traits.Any()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Validate derivatives argument
        derivatives, self.scope = validate_derivatives(
            bids_dir=self.bids_dir,
            derivatives=self.derivatives
        )

        self._layout = BIDSLayout(
            root=self.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=False
        )

        # Validate optional arguments
        filter_base = {}
        if self.task != []:
            task = validate_option(self.layout, self.task, kind='task')
            filter_base['task'] = task
        else:
            self.task = self.layout.get_tasks()
        if self.session != []:
            session = validate_option(self.layout, 
                                      self.session,
                                      kind='session')
            filter_base['session'] = session
        else:
            self.session = self.layout.get_sessions()
        if self.subject != []:
            subject = validate_option(self.layout, 
                                      self.subject,
                                      kind='subject')
            filter_base['subject'] = subject
        else:
            self.subject = self.layout.get_subjects()
        # Define query filters
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
            'space': 'MNI152NLin2009cAsym'
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
        fmri_prep = self.layout.get(scope=self.scope, **filter_fmri)
        fmri_prep_aroma = self.layout.get(scope=self.scope, **filter_fmri_aroma) # check type

        conf_raw = self.layout.get(scope=self.scope, **filter_conf)
        conf_json = self.layout.get(scope=self.scope, **filter_conf_json)

        # Validate correspondence between queried files
        entities = []
        for i, fmri_file in enumerate(fmri_prep):

            # reference common entities for preprocessed files
            if fmri_prep_aroma:
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
            root=self.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=True
        )

        for t in self.task:
            filter_fmri_tr = filter_fmri.copy()
            filter_fmri_tr['task'] = t

            try:
                example_file = layout_for_tr.get(**filter_fmri_tr)[0]
            except IndexError:
                raise MissingFile(f"no imaging file found for task {t}")
            tr_dict[t] = layout_for_tr.get_metadata(example_file.path)['RepetitionTime']
        # Create templates based on found files

        self._tr_dict = tr_dict

    @property
    def layout(self):
        return self._layout

    @property
    def tr_dict(self) -> dict:
        return self._tr_dict.copy()
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

    bids_dir = "/media/finc/Elements/fMRIDenoise_data/BIDS_LearningBrain_short_no_ICA/"
    ica_aroma = True

    grabber = BIDSGrab(bids_dir=bids_dir, ica_aroma=ica_aroma)
    result = grabber.run()

    print(result.outputs)