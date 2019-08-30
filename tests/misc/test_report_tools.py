import unittest as ut
from fmridenoise.pipelines import get_pipeline_path
from fmridenoise.utils.utils import load_pipeline_from_json
from fmridenoise.utils.report import get_pipeline_summary, YES, NO, NA

class TestPipelineSummary(ut.TestCase):

    def test_pipeline_1(self):
        pipeline = load_pipeline_from_json(get_pipeline_path('pipeline-24HMP_8Phys_SpikeReg_4GS'))
        summary = get_pipeline_summary(pipeline)
        for confound in summary:
            if confound['Confound'] == 'WM':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], YES)
                self.assertEqual(confound["Quadr. terms"], YES)
            elif confound['Confound'] == 'CSF':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], YES)
                self.assertEqual(confound["Quadr. terms"], YES)
            elif confound['Confound'] == 'GS':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], YES)
                self.assertEqual(confound["Quadr. terms"], YES)
            elif confound['Confound'] == 'aCompCor':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'ICA-AROMA':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'Spikes':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            else:
                raise ValueError(f'Unknown confound {confound}')

    def test_pipeline_2(self):
        pipeline = load_pipeline_from_json(get_pipeline_path('pipeline-ICA-AROMA_8Phys'))
        summary = get_pipeline_summary(pipeline)
        for confound in summary:
            if confound['Confound'] == 'WM':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], YES)
                self.assertEqual(confound["Quadr. terms"], YES)
            elif confound['Confound'] == 'CSF':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], YES)
                self.assertEqual(confound["Quadr. terms"], YES)
            elif confound['Confound'] == 'GS':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NO)
                self.assertEqual(confound["Quadr. terms"], NO)
            elif confound['Confound'] == 'aCompCor':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'ICA-AROMA':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'Spikes':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            else:
                raise ValueError(f'Unknown confound {confound}')

    def test_pipeline_3(self):
        pipeline = load_pipeline_from_json(get_pipeline_path('pipeline-24HMP_aCompCor_SpikeReg'))
        summary = get_pipeline_summary(pipeline)
        for confound in summary:
            if confound['Confound'] == 'WM':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NO)
                self.assertEqual(confound["Quadr. terms"], NO)
            elif confound['Confound'] == 'CSF':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NO)
                self.assertEqual(confound["Quadr. terms"], NO)
            elif confound['Confound'] == 'GS':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NO)
                self.assertEqual(confound["Quadr. terms"], NO)
            elif confound['Confound'] == 'aCompCor':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'ICA-AROMA':
                self.assertEqual(confound['Raw'], NO)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            elif confound['Confound'] == 'Spikes':
                self.assertEqual(confound['Raw'], YES)
                self.assertEqual(confound["Temp. deriv."], NA)
                self.assertEqual(confound["Quadr. terms"], NA)
            else:
                raise ValueError(f'Unknown confound {confound}')