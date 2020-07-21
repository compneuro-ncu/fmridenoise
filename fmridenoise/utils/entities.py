import re
import typing as t

from nipype.utils.filemanip import split_filename
import json

class EntityOverwriteException(Exception):
    def __init__(self, dictionary, key, *args, **kwargs):
        self.dictionary = dictionary
        self.key = key
        super(EntityOverwriteException, self).__init__(*args, **kwargs)

class EntityDict(dict):
    """
    Dictionary that returns None string if key is not in keys.
    Raises value error if element is tried to be overwritten with different value.
    """
    def __getitem__(self, key: str) -> t.Any:
        if key in self.keys():
            return super().__getitem__(key)
        else:
            return None

    def __setitem__(self, key: str, value: t.Any) -> None:
        if key in self.keys() and value != self[key]:
            raise EntityOverwriteException(self, key, f"Entity: {key} already exists in dictionary if it's intended user overwrite in other case"
                             f" there is probable flaw in entity structure which may cause undefined behavior")
        else:
            super().__setitem__(key, value)

    def __str__(self) -> str:
        return json.dumps(self)

    def overwrite(self, key: str, value: t.Any) -> None:  # TODO: Replace key, value with **kwargs
        """
        Sets value no matter what previous value was
        Args:
            key: Dictionary key
            value: New Value
        """
        super().__setitem__(key, value)

    def build_path(self, format_string):
        # TODO: Pretty powerful but naive solutions - will fail if any key in format string is not in dict
        format_string.format(**self)

    def build_filename(self, entities: t.Dict[str, bool]={
        "sub": True, "ses": False, "task": True, "space": False, "pipeline": False, "desc": False}) -> str:
        """
        Creates filename based on current entites in format:
        {entity0}-{entity_val0}_{entity1}-{entity_val1}_..._{suffix}.{extension}
        Args:
            entities: dictionary of entity name keys included in building filename and boolean values determining
            if value is mandatory in filename. If boolean value is true and entity value is available then
            it's included in filename. If boolean value is false then entity is included in filename if it has value.
            If boolean is value is true and there is no corresponding value then error is raised.
        Returns: filename created using selected entities, suffix (if available) and file extension (if available)
        """
        filename = ""
        for entity, required in entities.items():
            if required and self[entity] is None:
                raise Exception(f"Required entity {entity} is missing in entites: {self}")
            elif self[entity] is not None:
                filename += f"{entity}-{self[entity]}_"
        if self["suffix"] is not None:
            filename += self["suffix"]
        else:
            filename = filename.strip("_")
        if self["extension"] is not None:
            filename += "." + self["extension"]
        return filename


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
    _, basename, ext = split_filename(path)
    ret["extension"] = ext.strip('.')
    entities = list(map(lambda x: str.split(x, "-"), basename.split("_")))
    for entity in entities:
        if len(entity) == 1:
            ret['suffix'] = entity[0]
            continue
        try:
            ret[entity[0]] = entity[1]
        except EntityOverwriteException as e:
            raise Exception(f"While building EntityDict multiple instances of the same entity {e.key} occurred "
                            f"with values: {e.dictionary[e.key]} and {entity[1]}")

    return ret


if __name__ == '__main__':
    exploded = explode_into_entities(r"/mnt/Data/new_dataset/derivatives/fmriprep/sub-m02/func/sub-m02_task-prlrew_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
    print(exploded)