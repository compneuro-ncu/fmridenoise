import unittest as ut
from fmridenoise.pipelines import extract_pipeline_from_path

class ExtractPipelineTestCase(ut.TestCase):

    def test_search_1(self):
        path = '/tmp/fmridenoise/denoise/sub-m05_task-prlpun_space-MNI152NLin2009cAsym_pipeline-24HMP8PhysSpikeReg_desc-denoised_bold.nii.gz'
        expected_extraction = '24HMP8PhysSpikeReg'
        self.assertEqual(expected_extraction, extract_pipeline_from_path(path))

    def test_noresult(self):
        path = 'no pipeline path'
        expected_extraction = ""
        self.assertEqual(expected_extraction, extract_pipeline_from_path(path))