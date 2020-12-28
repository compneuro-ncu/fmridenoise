import tempfile
import atexit
import shutil
import os 
from os.path import join

automatic_cleanup = True
temp_dirs = []
base_dir = '/tmp/fmridenoise'


def mkdtemp(name: str) -> str:
    global temp_dirs
    try:
        ret = os.path.join(join(base_dir, name))
        os.makedirs(ret, exist_ok=True) # May be unsafe?
    except OSError:
        ret = tempfile.mkdtemp()
    temp_dirs.append(ret)
    return ret


def cleanup_tempdirs() -> None:
    global temp_dirs
    for directory in temp_dirs:
        shutil.rmtree(directory)
    temp_dirs = []
