# make sure that test can import fmridenoise if module is not installed in system
import sys
import os
try :
    pass
    #import fmridenoise
    #del fmridenoise
except ModuleNotFoundError:
    sys.path.insert(0, os.path.dirname((__file__)))

TEST_DIRECTORY = os.path.dirname(__file__)
