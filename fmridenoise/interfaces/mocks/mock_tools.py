import re
from nipype.utils.filemanip import split_filename
from ..mocks import bids_dir

class EntityDict(dict):
    """
    Dictionary that returns None string if key is not in keys.
    Raises value error if element is tried to be overwritten with different value.
    """
    def __getitem__(self, key):
        if key in self.keys():
            return super().__getitem__(key)
        else:
            return None

    def __setitem__(self, key, value):
        if key in self.keys() and value != self[value]:
            raise ValueError("There is probable flaw in entity structure which may cause undefined behavior")
        else:
            super().__setitem__(key, value)

    def overwrite(self, key, value):
        """
        Overwrites existing value at key with new value.
        Args:
            key: Existing dictionary key
            value: New Value
        """
        if key not in self.keys():
            raise ValueError(f"Key: {key} is not in EntityDict")
        super().__setitem__(key, value)


def explode_into_entities(path: str) -> EntityDict:
    """
    Revives all know entities/information from given path that are useful for fmridenoise.
    Args:
        path: path to file

    Returns:
        EntitiesDict with retrieved entities
    """
    ret = EntityDict()
    deriv = re.search("\/derivatives\/\w+", path)
    if deriv:
        ret['derivatives'] = deriv.string[deriv.regs[0][0]:deriv.regs[0][1]].strip(r'/derivatives')
        ret['dataset_directory'] = deriv.string[0:deriv.regs[0][0]]
    else:
        raise ValueError(f"Regex failed to search derivatives directory and dataset directory in {path}")
    _, basename, ext = split_filename(path)
    ret["extension"] = ext
    entities = list(map(lambda x: str.split(x, "-"), basename.split("_")))
    for entity in entities:
        if len(entity) == 1:
            ret['suffix'] = entity[0]
            continue
        ret[entity[0]] = entity[1]
    return ret


if __name__ == '__main__':
    exploded = explode_into_entities(r"/mnt/Data/new_dataset/derivatives/fmriprep/sub-m02/func/sub-m02_task-prlrew_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
    print(exploded)