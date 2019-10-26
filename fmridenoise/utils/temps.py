import tempfile
import atexit
import shutil
import os 

automatic_cleanup = True
temp_dirs = []
base_dir = '/tmp'

def mkdtemp(name: str) -> str:
    global temp_dirs
    try:
        ret = os.path.join(name)
        os.makedirs(ret, exist_ok=True) # May be unsafe?
    except OSError:
        ret = tempfile.mkdtemp()
    temp_dirs.append(ret)
    return ret


#@atexit.register    
def cleanup_tempdirs() -> None:
    global temp_dirs
    for directory in temp_dirs:
        shutil.rmtree(directory)
    temp_dirs = []