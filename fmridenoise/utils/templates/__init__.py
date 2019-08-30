from glob import glob
from os.path import join, dirname
from itertools import chain
def get_all_templates() -> list:
    current_dir = dirname(__file__)
    templates = list(chain(glob(join(current_dir, '*.html')), 
                           glob(join(current_dir, "*.css")),
                           glob(join(current_dir, "*.js"))))
    return templates

if __name__ == '__main__':
    print(get_all_templates())