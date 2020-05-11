from fmridenoise.interfaces.bids import BIDSValidate, MissingFile
import fmridenoise.pipelines as pipe
import unittest as ut
from os.path import join, dirname
from itertools import chain
# Data sets
testDir = dirname(__file__)
dummyDataPath = join(testDir, "dummy_complete")
dummyMissing = join(testDir, "dummy_missing_files")
pipelinesDir = dirname(pipe.__file__)
aromaPipelinesPaths = list(map(lambda name: join(pipelinesDir, name), ['pipeline-ICA-AROMA_8Phys.json']))
noAromaPipelinePaths = list(map(lambda name: join(pipelinesDir, name), ['pipeline-24HMP_aCompCor_SpikeReg.json']))


class BidsValidateFunctionsTestCase(ut.TestCase):

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
    pipelines = list(chain(aromaPipelinesPaths, noAromaPipelinePaths))
    bids_dir = dummyDataPath
    maxDiff = None

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
        for pipe_bidsVal, pipe_loaded in zip(self.bidsValidate._results["pipelines"], map(lambda x: pipe.load_pipeline_from_json(x), self.pipelines)):
            self.assertDictEqual(pipe_loaded, pipe_bidsVal)



if __name__ == '__main__':
    print(dummyDataPath)
    bidsValidate = BIDSValidate()
    bidsValidate.inputs.bids_dir = dummyDataPath
    bidsValidate.inputs.pipelines = [aromaPipelinesPaths[0], noAromaPipelinePaths[0]]
    bidsValidate.inputs.sessions = ['1']
    bidsValidate.inputs.subjects = ['01', '02']
    bidsValidate.inputs.tasks = ['audionback']
    bidsValidate.inputs.derivatives = ['fmriprep']
    # bidsValidate.run()
    print(BIDSValidate.validate_derivatives(dummyDataPath, 'fmriprep'))
