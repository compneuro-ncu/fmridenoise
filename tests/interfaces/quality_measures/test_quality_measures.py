import unittest as ut
from fmridenoise.interfaces import QualityMeasures
from tests import *
import os
import shutil
from os.path import join, dirname
class TestQualityMeasures(ut.TestCase):


    def setUp(self):
        self.temp = join(dirname(__file__), 'tmp')
        os.mkdir(self.temp)
        

    def tearDown(self):
        shutil.rmtree(self.temp)
        self.temp = None

    @ut.skip("No reason")
    def test_on_two_subject_data(self):
        """
        Data obtained from performing denoising with pipelines:
        pipeline-24HMP_8Phys_SpikeReg.json
        pipeline-24HMP_8Phys_SpikeReg_4GS.json
        """
        qc = QualityMeasures()

        qc.inputs.group_conf_summary = join(dirname(__file__), '2sub_conf.tsv')
        qc.inputs.group_corr_mat = join(dirname(__file__), '2sub_corr.npy')
        qc.inputs.distance_matrix = join(dirname(__file__), '2sub_distance.npy')
        qc.inputs.output_dir = self.temp
        qc.inputs.pipeline_name = "test"

#        results = qc.run()
