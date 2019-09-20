from fmridenoise.interfaces.bids import validate_derivatives, BIDSGrab
from os.path import dirname, join
import unittest as ut

# Datasets arguments
dn_dataset = {"bids_dir": join(dirname(__file__), 'dn9sub_fmriprep_dummy'),
              "derivatives": "fmriprep"}
lb_dataset = {"bids_dir": join(dirname(__file__), 'lb2sub_fmriprep_dummy'),
              "derivatives": "fmriprep"}

class TestBidsGrab(ut.TestCase):

    def test_bidsgrab_output_dn9sub(self):
        grabber = BIDSGrab(bids_dir=dn_dataset['bids_dir'],
                       derivatives='fmriprep')
        results = grabber.run()

        subjects = [f'm{sub:02}'for sub in list(range(2,10))]
        common_prefix = [
            join(dirname(__file__), 'dn9sub_fmriprep_dummy', 'derivatives',
                 'fmriprep', f'sub-{sub}/', 'func', f'sub-{sub}_task-{task}')
            for sub in subjects for task in ['prlpun', 'prlrew']]
        conf_json = [path_prefix + '_desc-confounds_regressors.json'
                     for path_prefix in common_prefix]
        conf_raw =  [path_prefix + '_desc-confounds_regressors.tsv'
                     for path_prefix in common_prefix]
        fmri_prep = [path_prefix + '_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz'
                     for path_prefix in common_prefix]
        entities = [{'datatype': 'func', 'subject': sub, 'task': task}
                    for sub in subjects for task in ['prlpun', 'prlrew']]
        tr_dict = {task:2 for task in ['prlpun', 'prlrew']}

        self.assertEqual(fmri_prep, results.outputs.fmri_prep)
        self.assertEqual(conf_json, results.outputs.conf_json)
        self.assertEqual(conf_raw, results.outputs.conf_raw)
        self.assertEqual(entities, results.outputs.entities)
        self.assertEqual(tr_dict, results.outputs.tr_dict)

    def test_validate_derivatives_output(self):
        derivatives_valid, scope = validate_derivatives(dn_dataset['bids_dir'],
                                                        dn_dataset['derivatives'])
        self.assertEqual(scope, ['fMRIPrep'])
        self.assertEqual(derivatives_valid, [join(dn_dataset['bids_dir'], 'derivatives/fmriprep')])

if __name__ == '__main__':

    pass
