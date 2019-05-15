import glob
import os.path as path
datasets = {}
dir = path.dirname(__file__)
for name in glob.glob(path.join(dir, '*')):
    if path.isdir(name):
        datasets[path.basename(name)] = path.abspath(name)