import unittest as ut
import typing as t
from itertools import product
from fmridenoise.utils.entities import build_path
from fmridenoise.interfaces.bids import BIDSGrab


class BidsGrabTestCase(ut.TestCase):

    path_patter = "[sub-{subject}_][ses-{session}_][task-{task}_][run-{run}_]fileName.extension"

    @classmethod
    def generatePaths(cls,
                      subjects: t.List[str] = (None,),
                      sessions: t.List[str] = (None,),
                      tasks: t.List[str] = (None,),
                      runs: t.List[str] = (None,)) -> t.List[str]:
        return [build_path({'subject': subject, 'session': session, 'task': task, 'run': run}, cls.path_patter, False)
                for subject, session, task, run in product(subjects, sessions, tasks, runs)]

    def test_select_one_valid(self):
        paths = self.generatePaths(['01', '02'], ['1', '2'], ['rest'], ['test', 'experiment'])
        file = BIDSGrab.select_one(paths, subject='01', session='1', task='rest', run='test')
        self.assertEqual('sub-01_ses-1_task-rest_run-test_fileName.extension', file)

    def test_select_one_multiple_finds(self):
        paths = self.generatePaths(['01', '02'], ['1', '2'], ['rest'], ['test', 'experiment'])
        with self.assertRaises(ValueError):
            BIDSGrab.select_one(paths, subject='01', session='1', task='rest', run=None)

    def test_select_one_none(self):
        paths = self.generatePaths(['01', '02'], ['1', '2'], ['rest'], ['test', 'experiment'])
        file = BIDSGrab.select_one(paths, subject='01', session='1', task='rest', run='nonexists')
        self.assertEqual('', file)
