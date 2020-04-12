import unittest
import tempfile
import copy
import os

import pandas as pd

from fmridenoise.interfaces.confounds import Confounds
from tests.interfaces.confounds.utils import (ConfoundsGenerator, 
    confound_filename, pipeline_null)

class TestConfounds(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.n_volumes = 100
        cls.n_tcompcor = 10
        cls.n_acompcor = 100
        cls.n_aroma = 20

        # Generate fake confounds
        cls.cg = ConfoundsGenerator(
            n_volumes=cls.n_volumes,
            n_tcompcor=cls.n_tcompcor,
            n_acompcor=cls.n_acompcor,
            n_aroma=cls.n_aroma
        )

        # BIDS variables
        cls.sub = '01'
        cls.ses = '1'
        cls.task = 'rest'
        
    def setUp(self):
        # Write confounds to file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.conf_filename_tsv = os.path.join(self.temp_dir.name, 
            confound_filename(sub=self.sub, ses=self.ses, task=self.task, ext='tsv'))
        self.conf_filename_json = os.path.join(self.temp_dir.name, 
            confound_filename(sub=self.sub, ses=self.ses, task=self.task, ext='json'))
        self.cg.confounds.to_csv(self.conf_filename_tsv, sep='\t', index=False)
        self.cg.meta_to_json(self.conf_filename_json)

    def tearDown(self):
        self.temp_dir.cleanup()

    @classmethod
    def tearDownClass(cls):
        pass

    def recreate_confounds_node(self, pipeline):
        node = Confounds(
            pipeline=pipeline,
            conf_raw=self.conf_filename_tsv,
            conf_json=self.conf_filename_json,
            subject=self.sub,
            task=self.task,
            session=self.ses,
            output_dir=self.temp_dir.name
        )
        return node

    def test_24hmp_filtering(self):
        '''Check if 24 motion parameters are correctly filtered from raw 
        confounds.
        '''
        pipeline = copy.deepcopy(pipeline_null)
        pipeline['confounds']['motion'] = {
            'temp_deriv': True,
            'quad_terms': True
        }

        # Run interface & load confounds
        node = self.recreate_confounds_node(pipeline)
        node.run()
        conf_prep = pd.read_csv(node._results['conf_prep'], sep='\t')

        # Recreate correct column names
        hmp_names = [f'{type_}_{axis}' 
            for type_ in ('trans', 'rot') for axis in ('x', 'y', 'z')]
        conf_names = {f'{hmp_name}{suffix}'
            for suffix in ('', '_derivative1', '_power2', '_derivative1_power2') 
            for hmp_name in hmp_names}

        self.assertEqual(conf_names, set(conf_prep.columns))
        self.assertEqual(conf_prep.shape, (self.n_volumes, 18)) 

    def test_8phys_4gs_filtering(self):
        '''Check if physiological signals and global signal are correctly 
        filtered from raw confounds. Physiological signals are white matter, csf
        signal.'''
        pipeline = copy.deepcopy(pipeline_null)
        pipeline['confounds']['wm'],  pipeline['confounds']['csf'], pipeline['confounds']['gs'] = \
            ({'temp_deriv': True, 'quad_terms': True}, ) * 3

        # Run interface & load confounds
        node = self.recreate_confounds_node(pipeline)
        node.run()
        conf_prep = pd.read_csv(node._results['conf_prep'], sep='\t')

        # Recreate correct column names
        phys_names = ['csf', 'global_signal', 'white_matter']
        conf_names = {f'{phys_name}{suffix}'
            for suffix in ('', '_derivative1', '_power2', '_derivative1_power2') 
            for phys_name in phys_names}

        self.assertEqual(conf_names, set(conf_prep.columns))
        self.assertEqual(conf_prep.shape, (self.n_volumes, 12)) 

if __name__ == '__main__':
    unittest.main()