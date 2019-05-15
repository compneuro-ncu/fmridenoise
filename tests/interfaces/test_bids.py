import sys
import tempfile
import shutil
import os
from tests.utils import create_dummy_bids
from fmridenoise.interfaces.bids import BIDSLoad
from nipype import Node
import unittest as ut
import tests.data as testData

class TestLoadBids(ut.TestCase):

    def test_load(self):
        outputs = [{'subject': '01'}, {'subject': '02'}, {'subject': '03'}, {'subject': '04'}, {'subject': '05'}, {'subject': '06'}, {'subject': '07'}, {'subject': '08'}, {'subject': '09'}, {'subject': '10'}, {'subject': '11'}, {'subject': '12'}, {'subject': '13'}]
        bl = Node(BIDSLoad(bids_dir=testData.datasets['one_ses_prep'], derivatives=True), name="TestBidsLoad")
        outs = bl.run()
        self.assertEqual(outs.outputs.entities, outputs)
