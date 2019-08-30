import unittest as ut
from fmridenoise.__main__ import parse_pipelines
import fmridenoise.pipelines as pipe
from os.path import dirname, join
from glob import glob
class TestPipelinesParser(ut.TestCase):

    pipelines_dir = dirname(pipe.__file__)
    all_pipelines_valid = set(glob(join(pipelines_dir, "*.json")))

    def test_parse_pipelines_without_custom(self):
        paths = parse_pipelines("all")
        self.assertSetEqual(self.all_pipelines_valid, paths)

    def test_parse_pipelines_custom(self):
        custom = {join(dirname(__file__), "custom_pipeline.json")}
        paths = parse_pipelines(custom)
        self.assertSetEqual(custom, paths)

    def test_parse_pipelines_mix(self):
        addition = join(dirname(__file__), "custom_pipeline.json")
        custom = self.all_pipelines_valid.copy()
        custom.add(addition)
        paths = parse_pipelines(custom)
        self.assertSetEqual(paths, custom)

    def test_parse_pipelines_known_pipeline(self):
        selected = "pipeline-24HMP_8Phys_SpikeReg_4GS"
        selected_path = {(join(self.pipelines_dir, selected) + ".json")}
        paths = parse_pipelines([selected]) # __main__ always return list of paths/selected pipelines names
        self.assertSetEqual(paths, selected_path)
