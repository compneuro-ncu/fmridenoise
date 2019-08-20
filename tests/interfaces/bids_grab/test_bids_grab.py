import sys
import tempfile
import shutil
import os
from fmridenoise.interfaces.bids import BIDSGrab
from nipype import Node
from os.path import dirname, join
import unittest as ut

TEST_DATASETS = {"NEW_FMRIPREP_DUMMY": join(dirname(__file__), 'new_fmriprep_dummy')}

class TestBidsGrab(ut.TestCase):
    

    def test_grab_entities_subjects(self):
        subject_outputs = [{'subject': '01'}, {'subject': '02'}, {'subject': '03'}, {'subject': '04'}, {'subject': '05'}, {'subject': '06'}, {'subject': '07'}, {'subject': '08'}, {'subject': '09'}, {'subject': '10'}, {'subject': '11'}, {'subject': '12'}, {'subject': '13'}]
        bl = Node(BIDSGrab(bids_dir=TEST_DATASETS['NEW_FMRIPREP_DUMMY']), name="TestBIDSGrab")
        outs = bl.run()
        bl_subjects = [{'subject': element['subject']} for element in outs.outputs.entities]
        self.assertEqual(bl_subjects, subject_outputs)


if __name__ == '__main__':
    import cProfile
    bl = Node(BIDSGrab(bids_dir=TEST_DATASETS['NEW_FMRIPREP_DUMMY']), name="TestBIDSGrab")
    bl.run()
    #   cProfile.run('bl.run()')