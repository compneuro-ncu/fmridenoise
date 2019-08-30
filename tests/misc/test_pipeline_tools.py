import fmridenoise.pipelines as pipe
import unittest as ut
from glob import glob
from os.path import dirname, join

class TestPipelinesTools(ut.TestCase):

    pipelines_dir = dirname(pipe.__file__)
    def test_get_pipeline_path(self):
        name = 'pipeline-24HMP_8Phys_SpikeReg_4GS'
        target = join(self.pipelines_dir, 'pipeline-24HMP_8Phys_SpikeReg_4GS.json')
        path = pipe.get_pipeline_path(name)
        self.assertEqual(target, path)


    def test_get_pipeline_path_fail(self):
        name = "not_exist.exe"
        self.assertRaises(ValueError, pipe.get_pipeline_name, name)


    def test_get_pipeline_name(self):
        path = join(self.pipelines_dir, 'pipeline-24HMP_8Phys_SpikeReg_4GS.json')
        target = 'pipeline-24HMP_8Phys_SpikeReg_4GS'
        self.assertEqual(pipe.get_pipeline_name(path), target)


    def test_get_pipeline_name_fail(self):
        invalid_name = join(self.pipelines_dir, "not_existing_pipeline.json")
        self.assertRaises(ValueError, pipe.get_pipeline_name, invalid_name)
        invalid_path = join(dirname(__file__), 'pipeline-24HMP_8Phys_SpikeReg_4GS.json')
        self.assertRaises(ValueError, pipe.get_pipeline_name, invalid_path)

    
    def test_get_all_pipeline_paths(self):
        from_glob = set(glob(join(self.pipelines_dir, "*.json")))
        from_get = pipe.get_pipelines_paths()
        self.assertEqual(from_glob, from_get)


    def test_get_pipelines_paths_fail(self):
        all_invalid = {'foo', 'bar'}
        self.assertRaises(ValueError, pipe.get_pipelines_paths, all_invalid)
        some_valid = {'pipeline-24HMP_8Phys_SpikeReg_4GS', 'not_valid'}
        self.assertRaises(ValueError, pipe.get_pipelines_paths, some_valid)
