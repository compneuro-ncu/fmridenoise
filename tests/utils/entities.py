import unittest as ut
from fmridenoise.utils.entities import explode_into_entities, EntityDict


class EntityDictTestCase(ut.TestCase):

    def test_setting_value(self):
        et = EntityDict({"test": 1})
        et["new"] = 2
        self.assertIn("test", et.keys())
        self.assertEqual(et["test"], 1)
        self.assertIn("new", et.keys())
        self.assertEqual(et["new"], 2)

    def test_overwriting_protection(self):
        et = EntityDict({"test": 1})
        self.assertRaises(Exception, et.__setitem__, key="test", value=2)

    def test_overwriting_same_value(self):
        et = EntityDict({"test": 1})
        et["test"] = 1

    def test_overwriting(self):
        et = EntityDict({"test": 1})
        et.overwrite("test", 2)
        self.assertIn("test", et.keys())
        self.assertEqual(et["test"], 2)

    def test_build_filename_default_args(self):
        et = EntityDict({
            "sub": 1,
            "ses": 1,
            "task": "None",
            "pipeline": "test",
            "desc": "test",
            "suffix": "bold",
            "extension": "json"})
        self.assertEqual(et.build_filename(), "sub-1_ses-1_task-None_pipeline-test_desc-test_bold.json")
        del et["ses"]
        self.assertEqual(et.build_filename(), "sub-1_task-None_pipeline-test_desc-test_bold.json")
        del et["suffix"]
        self.assertEqual(et.build_filename(), "sub-1_task-None_pipeline-test_desc-test.json")
        del et["extension"]
        self.assertEqual(et.build_filename(), "sub-1_task-None_pipeline-test_desc-test")

    def test_build_filename_mixed_postion(self):
        et = EntityDict({
            "sub": 1,
            "ses": 1,
            "task": "None",
            "pipeline": "test",
            "desc": "test",
            "suffix": "bold",
            "extension": "json"})
        self.assertEqual(et.build_filename(
            {"ses": False, "sub": True, "task": True, "pipeline": True, "desc": False}),
            "ses-1_sub-1_task-None_pipeline-test_desc-test_bold.json")

    def test_from_path_to_entites(self):
        path = "sub-1_ses-1_task-test_desc-aaa_t.exe"
        et = explode_into_entities(path)
        self.assertIn("sub", et.keys())
        self.assertIn("ses", et.keys())
        self.assertIn("task", et.keys())
        self.assertIn("desc", et.keys())
        self.assertIn("suffix", et.keys())
        self.assertIn("extension", et.keys())
        self.assertEqual(et["sub"], '1')
        self.assertEqual(et["ses"], '1')
        self.assertEqual(et["task"], 'test')
        self.assertEqual(et["desc"], 'aaa')
        self.assertEqual(et["suffix"], "t")
        self.assertEqual(et["extension"], "exe")

    def test_convert_forth_and_back(self):
        path = "sub-1_ses-1_task-test_desc-aaa_t.exe"
        self.assertEqual(path, explode_into_entities(path).build_filename())