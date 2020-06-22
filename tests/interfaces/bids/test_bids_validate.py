from bids import BIDSLayout
from fmridenoise.interfaces.bids import BIDSValidate, MissingFile
import fmridenoise.pipelines as pipe
import unittest as ut
from os.path import join, dirname
from typing import List


# Data sets
testDir = dirname(__file__)
dummyDataPath = join(testDir, "dummy_complete")
dummyMissing = join(testDir, "dummy_missing_files")
pipelinesDir = dirname(pipe.__file__)
aromaPipelinesPaths = [join(pipelinesDir, 'pipeline-ICA-AROMA_8Phys.json')]
noAromaPipelinePaths = [join(pipelinesDir, 'pipeline-24HMP_aCompCor_SpikeReg.json')]


class ValidateDerivativeTestCase(ut.TestCase):

    def test_validate_derivative_onValid(self) -> None:
        target_derivative_list = [join(dummyDataPath, "derivatives", "fmriprep")]
        target_scope = ['fMRIPrep']
        derivatives_list, scope = BIDSValidate.validate_derivatives(dummyDataPath, "fmriprep")
        self.assertListEqual(target_derivative_list, derivatives_list)
        self.assertListEqual(target_scope, scope)

    def test_validate_derivative_onMissingJson(self) -> None:
        self.assertRaises(MissingFile, BIDSValidate.validate_derivatives, dummyMissing, 'fmridenoise')

    def test_validate_derivative_onMissingDirectory(self) -> None:
        self.assertRaises(MissingFile, BIDSValidate.validate_derivatives, dummyMissing, 'notExisting')


class BidsValidateBasicPropertiesOnCompleteDataTestCase(ut.TestCase):

    derivatives = ["fmriprep"]
    tasks = ["audionback", "dualnback", "rest", "spatialnback"]
    sessions = ["1", "2", "3", "4"]
    subjects = ["01", "02"]
    pipelines = aromaPipelinesPaths + noAromaPipelinePaths
    pipelinesDicts = list(map(lambda x: pipe.load_pipeline_from_json(x), pipelines))
    bids_dir = dummyDataPath
    maxDiff = None

    @property
    def shouldContainAromaFiles(self) -> bool:
        return any(map(pipe.is_IcaAROMA, self.pipelinesDicts))

    @property
    def shouldContainNoAromaFiles(self) -> bool:
        return not all(map(pipe.is_IcaAROMA, self.pipelinesDicts))

    @classmethod
    def setUpClass(cls) -> None:
        cls.bidsValidate = BIDSValidate()
        cls.bidsValidate.inputs.bids_dir = cls.bids_dir
        cls.bidsValidate.inputs.derivatives = cls.derivatives
        cls.bidsValidate.inputs.tasks = cls.tasks
        cls.bidsValidate.inputs.sessions = cls.sessions
        cls.bidsValidate.inputs.subjects = cls.subjects
        cls.bidsValidate.inputs.pipelines = cls.pipelines
        cls.bidsValidate.run()

    def test_subject(self):
        self.assertListEqual(self.bidsValidate._results["subjects"], self.subjects)

    def test_tasks(self):
        self.assertListEqual(self.bidsValidate._results["tasks"], self.tasks)

    def test_sessions(self):
        self.assertListEqual(self.bidsValidate._results["sessions"], self.sessions)

    def test_pipelines(self):
        for pipe_bidsVal, pipe_loaded in zip(self.bidsValidate._results["pipelines"], self.pipelinesDicts):
            self.assertDictEqual(pipe_loaded, pipe_bidsVal)

    def test_aromaFiles(self):
        if self.shouldContainAromaFiles:
            filesCount = len(self.subjects) * len(self.sessions) * len(self.tasks)
            self.assertEqual(filesCount, len(self.bidsValidate._results["fmri_prep_aroma"]))
        else:
            self.assertEqual(0, len(self.bidsValidate._results["fmri_prep_aroma"]))

    def test_noAromaFiles(self):
        if self.shouldContainNoAromaFiles:
            filesCount = len(self.subjects) * len(self.sessions) * len(self.tasks)
            self.assertEqual(filesCount, len(self.bidsValidate._results["fmri_prep"]))
        else:
            self.assertEqual(0, len(self.bidsValidate._results["fmri_prep"]))

    def test_test_tr(self):
        for task in self.tasks:
            self.assertEqual(2, self.bidsValidate._results["tr_dict"][task])  # a magical number - 2


class BidsValidateNoAromaOnCompleteDataTestCase(BidsValidateBasicPropertiesOnCompleteDataTestCase):
    derivatives = ["fmriprep"]
    tasks = ["audionback", "dualnback", "rest", "spatialnback"]
    sessions = ["1", "2", "3", "4"]
    subjects = ["01", "02"]
    pipelines = noAromaPipelinePaths
    pipelinesDicts = list(map(lambda x: pipe.load_pipeline_from_json(x), pipelines))
    bids_dir = dummyDataPath
    maxDiff = None


class BidsValidateOnlyAromaOnCompleteDataTestCase(BidsValidateBasicPropertiesOnCompleteDataTestCase):
    derivatives = ["fmriprep"]
    tasks = ["audionback", "dualnback", "rest", "spatialnback"]
    sessions = ["1", "2", "3", "4"]
    subjects = ["01", "02"]
    pipelines = aromaPipelinesPaths
    pipelinesDicts = list(map(lambda x: pipe.load_pipeline_from_json(x), pipelines))
    bids_dir = dummyDataPath
    maxDiff = None


class ValidateFilesOnMissingTestCase(ut.TestCase):
    """
    TODO: Consider adding mutating test covering all possible parameter configurations
    """
    derivatives = ["fmriprep"]
    tasks = ["audionback", "dualnback", "rest", "spatialnback"]
    sessions = ["1", "2", "3", "4"]
    subjects = ["01", "02"]
    pipelines = aromaPipelinesPaths + noAromaPipelinePaths
    pipelinesDicts = list(map(lambda x: pipe.load_pipeline_from_json(x), pipelines))
    bids_dir = dummyMissing
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        # Validate derivatives argument
        derivatives, scope = BIDSValidate.validate_derivatives(
            bids_dir=cls.bids_dir,
            derivatives=cls.derivatives
        )

        # Load layout
        cls.layout = BIDSLayout(
            root=cls.bids_dir,
            derivatives=derivatives,
            validate=True,
            index_metadata=False
        )

    def parametrizedTest(self,
                         tasks: List[str],
                         sessions: List[str],
                         subjects: List[str],
                         include_aroma: bool,
                         include_no_aroma: bool,
                         should_pass: bool):
        if not should_pass:
            with self.assertRaises(MissingFile):
                BIDSValidate.validate_files(
                    layout=self.layout,
                    tasks=tasks,
                    sessions=sessions,
                    subjects=subjects,
                    include_aroma=include_aroma,
                    include_no_aroma=include_no_aroma
                )
        else:
            BIDSValidate.validate_files(
                layout=self.layout,
                tasks=tasks,
                sessions=sessions,
                subjects=subjects,
                include_aroma=include_aroma,
                include_no_aroma=include_no_aroma
            )

    def test_task_dualnback_sub_01_ses_1_aromta_t_PASS(self):
        self.parametrizedTest(
            tasks=['dualnback'],
            sessions=['1'],
            subjects=['01'],
            include_no_aroma=True,
            include_aroma=True,
            should_pass=True
        )

    def test_task_audionback_sub_01_ses_1_aromta_f_PASS(self):
        self.parametrizedTest(
            tasks=['audionback'],
            sessions=['1'],
            subjects=['01'],
            include_no_aroma=True,
            include_aroma=False,
            should_pass=True
        )

    # test against missing aroma files
    def test_task_audionback_sub_01_ses_1_aroma_t_FAIL(self):
        self.parametrizedTest(
            tasks=['audionback'],
            sessions=['1'],
            subjects=['01'],
            include_no_aroma=True,
            include_aroma=True,
            should_pass=False
        )

    def test_task_audionback_sub_01_ses_2_aroma_t_PASS(self):
        self.parametrizedTest(
            tasks=['audionback'],
            sessions=['2'],
            subjects=['01'],
            include_no_aroma=True,
            include_aroma=True,
            should_pass=True
        )

    # test against missing session
    def test_task_audionback_sub_01_02_ses_2_aroma_t_FAIL(self):
        self.parametrizedTest(
            tasks=['audionback'],
            sessions=['2'],
            subjects=['01', '02'],
            include_no_aroma=True,
            include_aroma=True,
            should_pass=False
        )

    # test against missing subject
    def test_task_audionback_sub_03_ses_2_aroma_t_FAIL(self):
        self.parametrizedTest(
            tasks=['audionback'],
            sessions=['2'],
            subjects=['03'],
            include_no_aroma=True,
            include_aroma=True,
            should_pass=False
        )
