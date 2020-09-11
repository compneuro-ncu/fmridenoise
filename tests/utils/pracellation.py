import unittest as ut
import fmridenoise.parcellation
from fmridenoise.parcellation import get_parcellation_file_path
from os.path import join, dirname


class ParcellationHelpers(ut.TestCase):

    def test_get_MNI152Nlin6Asym(self):
        path = get_parcellation_file_path('MNI152NLin6Asym')
        self.assertEqual(path,
                         join(dirname(fmridenoise.parcellation.__file__),
                              'tpl-MNI152NLin6Asym_res-01_atlas-Schaefer2018_desc-200Parcels7Networks_dseg.nii.gz'))

    def test_get_MINI152NLin2009cAsym(self):
        path = get_parcellation_file_path('MNI152NLin2009cAsym')
        self.assertEqual(path,
                         join(dirname(fmridenoise.parcellation.__file__),
                              'tpl-MNI152NLin2009cAsym_res-01_atlas-Schaefer2018_desc-200Parcels7Networks_dseg.nii.gz'))
