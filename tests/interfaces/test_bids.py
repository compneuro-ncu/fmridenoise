import sys
import tempfile
import shutil
import os
from tests.utils import create_dummy_bids
from fmridenoise.interfaces.bids import BIDSGrab
from nipype import Node
import unittest as ut
import tests.data as testData

class TestBidsGrab(ut.TestCase):

    def test_grab_entities_subjects(self):
        subject_outputs = [{'subject': '01'}, {'subject': '02'}, {'subject': '03'}, {'subject': '04'}, {'subject': '05'}, {'subject': '06'}, {'subject': '07'}, {'subject': '08'}, {'subject': '09'}, {'subject': '10'}, {'subject': '11'}, {'subject': '12'}, {'subject': '13'}]
        bl = Node(BIDSGrab(bids_dir=testData.datasets['one_ses_prep']), name="TestBIDSGrab")
        outs = bl.run()
        bl_subjects = [{'subject': element['subject']} for element in outs.outputs.entities]
        self.assertEqual(bl_subjects, subject_outputs)
