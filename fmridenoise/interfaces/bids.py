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
    conf_json = OutputMultiPath(File)  # TODO: Kamil check
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

        import json
        from bids import BIDSLayout

        def validate_derivatives(bids_dir, derivatives):
            """ Validate derivatives argument provided by the user.

            Args:
                bids_dir: list
                    Path to bids root directory.
                derivatives: str or list(str)
                    Derivatives to use for denoising.

            Returns:
                derivatives_: list
                    Validated derivatives list.
                scope: list
                    Right scope keyword used in pybids query.
            """

            if isinstance(derivatives, str):
                derivatives_ = [derivatives]
            else:
                derivatives_ = derivatives

            # Create full paths to derivatives folders
            derivatives_ = [os.path.join(bids_dir, 'derivatives', d)
                            for d in derivatives_]

            # Establish right scope keyword for arbitrary packages
            scope = []
            for derivative_path in derivatives_:
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

            return derivatives_, scope

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

            option_ = option
            for option_item in option_:
                if option_item not in option_all:
                    raise ValueError(f'{kind} {option_item} is not found')

            return option_

        # Validate derivatives argument
        derivatives, scope = validate_derivatives(
            bids_dir=self.inputs.bids_dir,
            derivatives=self.inputs.derivatives
        )

        layout = BIDSLayout(
            root=self.inputs.bids_dir,
            validate=True,
            derivatives=derivatives
        )

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
        keys_entities = ['task', 'session', 'subject', 'datatype']

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
        }  # for later
        filter_conf_json = {
            'extension': 'json',
            'suffix': 'regressors',
            'desc': 'confounds',
        }

        filter_fmri.update(filter_base)

        ########################################################################
        ### SOLUTION FOR LATER #################################################
        ########################################################################
        # filter_fmri_aroma.update(filter_base)
        # filter_conf.update(filter_base)
        # filter_conf_json.update(filter_base)

        # # Grab all requested files
        # fmri_prep = layout.get(scope=scope, **filter_fmri)
        # if self.inputs.ica_aroma:
        #     fmri_prep_aroma = layout.get(scope=scope, **filter_fmri_aroma)
        # conf_raw = layout.get(scope=scope, **filter_conf)
        # conf_json = layout.get(scope=scope, **filter_conf_json)
        ########################################################################
        ########################################################################
        ########################################################################

        fmri_prep, fmri_prep_aroma, conf_raw, conf_json, entities = ([] for _ in
                                                                     range(5))

        for fmri_file in layout.get(scope=scope, **filter_fmri):

            entity_bold = fmri_file.get_entities()

            # Look for corresponding confounds file
            filter_entities = {key: value
                               for key, value in entity_bold.items()
                               if key in keys_entities}

            # Constraining search
            filter_conf.update(filter_entities)
            filter_conf_json.update(filter_entities)

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

                conf_json_file = conf_json_file[0]

            if self.inputs.ica_aroma:
                filter_fmri_aroma.update(
                    filter_entities)  # Add specific fields to constrain search
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
        self._results['fmri_prep_aroma'] = fmri_prep_aroma
        self._results['conf_raw'] = conf_raw
        self._results['conf_json'] = conf_json
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
            sub_num = entity['subject']  # TODO: Add support for sessions
            session_num = entity[
                'session']  # TODO: Add conditionals if no sessions
            basedir, basename, ext = split_filename(in_file)
            path = f"{base_dir}/derivatives/fmridenoise/sub-{sub_num}/ses-{session_num}"
            os.makedirs(path, exist_ok=True)
            out_fname = f"{path}/{basename}_pipeline-{self.inputs.pipeline_name}{ext}"
            copyfile(in_file, out_fname, copy=True)
            out_files.append(out_fname)
        return {'out_file': out_files}


# --- TESTS

if __name__ == '__main__':
    bids_dir = '/media/finc/Elements/fMRIDenoise_data/BIDS_LearningBrain_short/'
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