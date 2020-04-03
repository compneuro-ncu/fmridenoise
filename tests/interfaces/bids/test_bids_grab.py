from fmridenoise.interfaces.bids import validate_derivatives, BIDSGrab
from os.path import dirname, join
import unittest as ut

# Datasets
dn_dataset = {"bids_dir": join(dirname(__file__), 'dn3sub_fmriprep_dummy'),
              "derivatives": "fmriprep"}
lb_dataset = {"bids_dir": join(dirname(__file__), 'lb2sub_fmriprep_dummy'),
              "derivatives": "fmriprep"}

class TestBidsGrab(ut.TestCase):

    def test_bidsgrab_output_dn3sub(self):

        # Create correct output
        subjects = [f'm{sub:02}'for sub in list(range(2,5))]
        common_prefix = [
            join(dirname(__file__), 'dn3sub_fmriprep_dummy', 'derivatives',
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

        # No flags
        grabber = BIDSGrab(bids_dir=dn_dataset['bids_dir'])
        results = grabber.run()
        self.assertEqual(fmri_prep, results.outputs.fmri_prep)
        self.assertEqual(conf_json, results.outputs.conf_json)
        self.assertEqual(conf_raw, results.outputs.conf_raw)
        self.assertEqual(entities, results.outputs.entities)
        self.assertEqual(tr_dict, results.outputs.tr_dict)

        # Participant flag
        grabber = BIDSGrab(bids_dir=dn_dataset['bids_dir'], subject=['m03'])
        results = grabber.run()
        subfilter = lambda l: list(filter(lambda x: 'm03' in x, l))
        self.assertEqual(subfilter(fmri_prep), results.outputs.fmri_prep)
        self.assertEqual(subfilter(conf_json), results.outputs.conf_json)
        self.assertEqual(subfilter(conf_raw), results.outputs.conf_raw)
        self.assertEqual(
            [entity for entity in entities if entity['subject'] == 'm03'],
            results.outputs.entities
        )
        self.assertEqual(tr_dict, results.outputs.tr_dict)

        # Task flag
        grabber = BIDSGrab(bids_dir=dn_dataset['bids_dir'], task=['prlpun'])
        results = grabber.run()
        taskfilter = lambda l: list(filter(lambda x: 'prlpun' in x, l))
        self.assertEqual(taskfilter(fmri_prep), results.outputs.fmri_prep)
        self.assertEqual(taskfilter(conf_json), results.outputs.conf_json)
        self.assertEqual(taskfilter(conf_raw), results.outputs.conf_raw)
        self.assertEqual(
            [entity for entity in entities if entity['task'] == 'prlpun'],
            results.outputs.entities
        )
        self.assertEqual({'prlpun': 2}, results.outputs.tr_dict)

    def test_validate_derivatives_output(self):
        derivatives_valid, scope = validate_derivatives(dn_dataset['bids_dir'],
                                                        dn_dataset['derivatives'])
        self.assertEqual(scope, ['fMRIPrep'])
        self.assertEqual(derivatives_valid, [join(dn_dataset['bids_dir'], 'derivatives/fmriprep')])
