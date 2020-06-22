from fmridenoise.utils.json_validator import is_valid
from tests.utils import pipeline_null

import copy
import unittest
import itertools


class TestPipelineValidation(unittest.TestCase):

    def setUp(self):
        self.pipeline = copy.deepcopy(pipeline_null)
        self.pipeline['name'] = 'Null'
        self.pipeline['description'] = 'Null pipeline'


    def test_null_pipeline(self):
        '''Ensure that null pipeline is valid.'''
        self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_pipeline_name_missing(self):
        del self.pipeline['name']
        self.assertFalse(is_valid(self.pipeline, silent=True))


    def test_pipeline_name_empty_string(self):
        self.pipeline['name'] = ''
        self.assertFalse(is_valid(self.pipeline, silent=True))
    

    def test_missing_description(self):
        '''Missing description should be valid.'''
        del self.pipeline['description']
        self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_missing_confound(self):
        for confound_name in ['white_matter', 'csf', 'global_signal', 
                              'motion', 'acompcor']:
            del self.pipeline['confounds'][confound_name]
            self.assertFalse(is_valid(self.pipeline, silent=True))
            self.setUp()


    def test_correct_confound_dict_values(self):
        '''Test all combinations of True / False values for confound dict.'''
        for confound_name in ['white_matter', 'csf', 'global_signal', 'motion']:
            for c in itertools.combinations_with_replacement([True, False], 4):
                confound_dict = self.pipeline['confounds'][confound_name] 
                confound_dict.update(zip(confound_dict, c))
                self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_incorrect_confound_dict_values(self):
        '''Test wrong values for confound dict options.'''
        for confound_name in ['white_matter', 'csf', 'global_signal', 'motion']:
            for type_ in ['raw', 'derivative1', 'power2', 'derivative1_power2']:
                for val in [1, 0, 'False', 'True', None]:
                    self.pipeline['confounds'][confound_name][type_] = val 
                    self.assertFalse(is_valid(self.pipeline, silent=True))
                    self.setUp()


    def test_missing_confound_type(self):
        '''Keys 'raw', 'derivative1', 'power2' and 'derivative1_power2' are 
        mandatory for confound dict.'''
        for confound_name in ['white_matter', 'csf', 'global_signal', 'motion']:
            for type_ in ['raw', 'derivative1', 'power2', 'derivative1_power2']:
                del self.pipeline['confounds'][confound_name][type_]
                self.assertFalse(is_valid(self.pipeline, silent=True))
                self.setUp()


    def test_correct_acompcor(self):
        self.pipeline['confounds']['acompcor'] = True
        self.assertTrue(is_valid(self.pipeline, silent=True))
        self.pipeline['confounds']['acompcor'] = False
        self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_incorrect_acompcor(self):
        for val in [1, 0, 'False', 'True', None, {'key': True}, 0.1, list()]:
            self.pipeline['confounds']['acompcor'] = val
            self.assertFalse(is_valid(self.pipeline, silent=True))


    def test_correct_aroma(self):
        self.pipeline['aroma'] = True
        self.assertTrue(is_valid(self.pipeline, silent=True))
        self.pipeline['aroma'] = False
        self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_incorrect_aroma(self):
        for val in [1, 0, 'False', 'True', None, {'key': True}, 0.1, list()]:
            self.pipeline['aroma'] = val
            self.assertFalse(is_valid(self.pipeline, silent=True))


    def test_correct_spikes_dict_values(self):
        for fd_val in [0.01, 1, 2.165, 5.94, 20]:
            for dvars_val in [0.01, 1, 2.165, 5.94, 20]:
                self.pipeline['spikes'] = {
                    'fd_th': fd_val,
                    'dvars_th': dvars_val
                }
                self.assertTrue(is_valid(self.pipeline, silent=True))


    def test_incorrect_spikes_dict_values(self):
        for fd_val in [-1, True, False, None, 'True', '1', '2.15']:
            for dvars_val in [-1, True, False, None, 'True', '1', '2.15']:
                self.pipeline['spikes'] = {
                    'fd_th': fd_val,
                    'dvars_th': dvars_val
                }
                self.assertFalse(is_valid(self.pipeline, silent=True))


    def test_incorrect_spikes_value(self):
        '''Value for 'spikes' key can be either False or spikes dict'''
        for val in [True, None, 'True', 'False', 0, 1.321]:
            self.pipeline['spikes'] = val
            self.assertFalse(is_valid(self.pipeline, silent=True))


    def test_missing_spikes_dict_key(self):
        for key in ['fd_th', 'dvars_th']:
            self.pipeline['spikes'] = {key: 1.321}
            self.assertFalse(is_valid(self.pipeline, silent=True))
    

if __name__ == '__main__':
    unittest.main()