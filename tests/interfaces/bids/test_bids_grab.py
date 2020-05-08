from fmridenoise.interfaces.bids import BIDSValidate, MissingFile
import fmridenoise.pipelines as pipe
import unittest as ut
from os.path import join, dirname

# Data sets
testDir = dirname(__file__)
dummyDataPath = join(testDir, "dummy_complete")
dummyMissing = join(testDir, "dummy_missing_files")
pipelinesDir = dirname(pipe.__file__)
aromaPipelinesDicts = list(map(lambda name: join(pipelinesDir, name), ['pipeline-ICA-AROMA_8Phys.json']))
noAromaPipelineDicts = list(map(lambda name: join(pipelinesDir, name), ['pipeline-24HMP_aCompCor_SpikeReg.json']))


class BidsValidateFunctionsTestCase(ut.TestCase):

    def test_validate_derivative_onValid(self):
        target_derivative_list = [join(dummyDataPath, "derivatives", "fmriprep")]
        target_scope = ['fMRIPrep']
        derivatives_list, scope = BIDSValidate.validate_derivatives(dummyDataPath, "fmriprep")
        self.assertListEqual(target_derivative_list, derivatives_list)
        self.assertListEqual(target_scope, scope)

    def test_validate_derivative_onMissingJson(self):
        self.assertRaises(MissingFile, BIDSValidate.validate_derivatives, dummyMissing, 'fmridenoise')

    def test_validate_derivative_onMissingDirectory(self):
        self.assertRaises(MissingFile, BIDSValidate.validate_derivatives, dummyMissing, 'notExisting')




class BidsValidateTestCase(ut.TestCase):
    pass


if __name__ == '__main__':
    print(dummyDataPath)
    bidsValidate = BIDSValidate()
    bidsValidate.inputs.bids_dir = dummyDataPath
    bidsValidate.inputs.pipelines = [aromaPipelinesDicts[0], noAromaPipelineDicts[0]]
    bidsValidate.inputs.sessions = ['1']
    bidsValidate.inputs.subjects = ['01', '02']
    bidsValidate.inputs.tasks = ['audionback']
    bidsValidate.inputs.derivatives = ['fmriprep']
    # bidsValidate.run()
    print(BIDSValidate.validate_derivatives(dummyDataPath, 'fmriprep'))
