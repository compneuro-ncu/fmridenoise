import unittest
import tempfile
import copy
import os

import pandas as pd
import numpy as np
from nipype import Node
from traits.trait_base import Undefined

from fmridenoise.interfaces.denoising import Denoise
from tests.utils import fmri_prep_filename, confound_filename, pipeline_null


class TestDenoising(unittest.TestCase):
    sub = '01'
    ses = '1'
    task ='test'

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = tempfile.TemporaryDirectory()

        self.fmri_prep = os.path.join(
            self.temp_dir.name,
            fmri_prep_filename(self.sub, self.ses, self.task, False))
        self.fmri_prep_aroma = os.path.join(
            self.temp_dir.name,
            fmri_prep_filename(self.sub, self.ses, self.task, True))
        self.conf_prep = os.path.join(
            self.temp_dir.name,
            confound_filename(self.sub, self.ses, self.task, ext='tsv'))

        # Create empty files
        for file in (self.fmri_prep, self.fmri_prep_aroma):
            open(file, 'a').close()
        pd.DataFrame().to_csv(self.conf_prep, sep='\t', index=False)

        self.pipeline = copy.deepcopy(pipeline_null)
        self.task = self.task
        self.tr_dict = {self.task: 2}

    def tearDown(self):
        self.temp_dir.cleanup()
        self.out_dir.cleanup()

    def test_missing_aroma_files_on_noaroma_pipeline(self):
        self.pipeline['aroma'] = False

        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name
        )

        def _(runtime):
            denoise._validate_fmri_prep_files()
            return  runtime

        denoise._run_interface = _
        denoise.run()

    def test_missing_noaroma_files_on_aroma_pipeline(self):
        self.pipeline['aroma'] = True

        denoise = Denoise(
            fmri_prep_aroma=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name
        )

        def _(runtime):
            denoise._validate_fmri_prep_files()
            return runtime

        denoise._run_interface = _
        denoise.run()

    def test_missing_both_fmri_prep_files(self):
        '''Expect FileNotFoundError when neither fmri_prep nor fmri_prep_aroma
        were specified.'''
        denoise = Denoise(
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
        )
        with self.assertRaises(FileNotFoundError):
            denoise.run()

    def test_missing_fmri_prep(self):
        '''Expect FileNotFoundError if pipeline without aroma is selected but 
        only fmri_prep_aroma is provided.'''
        self.pipeline['aroma'] = False
        denoise = Denoise(
            fmri_prep_aroma=self.fmri_prep_aroma,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
        )
        with self.assertRaises(FileNotFoundError):
            denoise.run()

    def test_missing_fmri_prep_aroma(self):
        '''Expect FileNotFoundError if pipeline with aroma is selected but only
        fmri_prep file (without aroma) is provided.'''
        self.pipeline['aroma'] = True
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
        )
        with self.assertRaises(FileNotFoundError):
            denoise.run()

    def test_empty_confounds(self):
        '''Expect that clean_image will receive None as value for confounds 
        keyword when conf_prep is empty confounds table.'''
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
        )
        denoise._load_confouds()
        self.assertEqual(denoise._confounds, None)

    def test_non_empty_confounds(self):
        '''Expect that clean_image will receive correctly loaded confounds as 
        numpy.ndarray.'''
        conf_prep = pd.DataFrame(np.random.random((100, 2)))
        conf_prep.to_csv(self.conf_prep, sep='\t', index=False)
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
        )
        denoise._load_confouds()
        self.assertEqual(denoise._confounds.shape, (100, 2))

    def test_no_bandpass_filtering(self):
        '''Expect that if low_pass, high_pass and tr_dict are not provided 
        _filtering_kwargs attribute containg optional arguments for clean_img 
        function will be empty dictionary (filtering not specified).'''
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name
        )
        denoise._validate_filtering('test')
        self.assertEqual(denoise._filtering_kwargs, dict())

    def test_banpass_filtering(self):
        '''Expect that if low_pass and high_pass arguments are provided, then 
        _filtering_kwargs dict will contain correct keywords for clean_img 
        function.'''
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
            tr_dict=self.tr_dict,
            high_pass=1/128,
            low_pass=1/5
        )
        denoise._validate_filtering('test')
        self.assertEqual({'high_pass': 1/128, 'low_pass': 1/5, 't_r': 2},
                         denoise._filtering_kwargs)

    def test_missing_tr_dict(self):
        '''Expect an Exception if either high_pass or low_pass is provided, but
        tr_dict is missing (clean_img require tr if filtering is requested).'''
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
            high_pass=1/128,
        )
        with self.assertRaises(TypeError):
            denoise._validate_filtering()
            
    def test_incorrect_tr_dict(self):
        '''Expect KeyError if tr_dict does not contain requested task.'''
        self.tr_dict = {'another_task': 2}
        denoise = Denoise(
            fmri_prep=self.fmri_prep,
            conf_prep=self.conf_prep,
            pipeline=self.pipeline,
            output_dir=self.out_dir.name,
            tr_dict=self.tr_dict,
            high_pass=1/128,
            low_pass=1/5
        )
        with self.assertRaises(KeyError):
            denoise._validate_filtering('test')


class MinorWorkflowIntegrationTestCase(unittest.TestCase):
    """Tests checking input integration at nodes level"""
    sub = '01'
    ses = '1'
    task = 'test'

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = tempfile.TemporaryDirectory()

        self.fmri_prep = os.path.join(
            self.temp_dir.name,
            fmri_prep_filename(self.sub, self.ses, self.task, False))
        self.fmri_prep_aroma = os.path.join(
            self.temp_dir.name,
            fmri_prep_filename(self.sub, self.ses, self.task, True))
        self.conf_prep = os.path.join(
            self.temp_dir.name,
            confound_filename(self.sub, self.ses, self.task, ext='tsv'))

        # Create empty files
        for file in (self.fmri_prep, self.fmri_prep_aroma):
            open(file, 'a').close()
        pd.DataFrame().to_csv(self.conf_prep, sep='\t', index=False)

        self.pipeline = copy.deepcopy(pipeline_null)
        self.task = self.task
        self.tr_dict = {self.task: 2}

        def _(self, runtime):
            self._validate_fmri_prep_files()
            return runtime
        Denoise._run_interface = _

    def tearDown(self):
        self.temp_dir.cleanup()
        self.out_dir.cleanup()

    def build_node(self) -> Node:
        denoise_node = Node(name='InputSource', interface=Denoise())
        denoise_node.inputs.conf_prep = self.conf_prep
        denoise_node.inputs.pipeline = self.pipeline
        denoise_node.inputs.output_dir = self.out_dir.name
        denoise_node.inputs.tr_dict = self.tr_dict
        denoise_node.inputs.fmri_prep_aroma = self.fmri_prep_aroma
        denoise_node.inputs.fmri_prep = self.fmri_prep
        return denoise_node

    def test_missing_aroma_files_on_noaroma_pipeline(self):
        self.pipeline['aroma'] = False
        self.fmri_prep_aroma = Undefined
        node = self.build_node()
        node.run()
