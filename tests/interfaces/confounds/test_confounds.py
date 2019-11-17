import unittest as ut
from fmridenoise.interfaces.confounds import Confounds
from nipype import Node
from fmridenoise.pipelines import get_pipelines_paths, load_pipeline_from_json
from os.path import dirname, join
from os import remove
from glob import glob
import json

class TestConfounds(ut.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        pipeline = load_pipeline_from_json(get_pipelines_paths({'pipeline-ICA-AROMA_8Phys'}).pop())
        conf_raw = join(dirname(__file__),
        "sub-01_ses-1_task-audionback_desc-confounds_regressors.tsv")
        conf_json = join(dirname(__file__),
        "sub-01_ses-1_task-audionback_desc-confounds_regressors.json")
        subject = '01'
        session = '1'
        task = 'audionback'
        output_dir = dirname(__file__)
        cls.confound = Confounds(
            output_dir = output_dir,
            pipeline = pipeline,
            conf_raw=conf_raw,
            conf_json=conf_json,
            subject=subject,
            session=session,
            task=task
        )

    @classmethod
    def tearDownClass(cls) -> None:
        to_remove = glob(join(dirname(__file__), "*pipeline*"))
        for path in to_remove:
            remove(path)

    def test_valid_paths(self) -> None:
        node = Node(self.confound, name='TestConfounds')
        node.run()
        self.assertEqual(
            node.get_output('conf_prep'),
            join(dirname(__file__), "sub-01_ses-1_task-audionback_desc-confounds_regressors_prep_pipeline-ICA-AROMA_8Phys.tsv"))
        self.assertEqual(
            node.get_output('conf_summary_json_file'),
            join(dirname(__file__), "sub-01_ses-1_task-audionback_desc-confounds_regressors_prep_pipeline-ICA-AROMA_8Phys_summary_dict.json"))

    def test_valid_json_content(self) -> None:
        expected_dict = {
            "subject": ["01"],
            "session": ["1"],
            "task": ["01"],
            "mean_fd": [0.10787703340943952],
            "max_fd": [1.14735715],
            "n_spikes": [0.0],
            "perc_spikes": [0.0],
            "n_conf": [6.0],
            "include": [1.0]
        }
        node = Node(self.confound, name='TestConfounds')
        node.run()
        with open(node.get_output('conf_summary_json_file'), 'r') as file:
            result = json.load(file)
            self.assertEqual(expected_dict, result)
