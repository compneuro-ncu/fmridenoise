import json
import jsonschema
import copy
from os.path import exists
_pipeline_valid_keys = ["name", "descrtiption", "confounds"]
type_checker = jsonschema.Draft4Validator.VALIDATORS

def load_pipeline_from_json(json_path: str) -> dict:
    """
    Loads json file and prepares it for further use (e.g. assures proper types interpretation)
    :param json_path: path to json file
    :return: jsonlike dictionary
    """
    if not exists(json_path):
        raise IOError(f"File '{json_path}' does not exists!")
    with open(json_path, 'r') as json_file:
        js = json.load(json_file)
    js = swap_booleans(js, inplace=True)
    return js


def is_booleanlike(value) -> bool:
    """
    Checks if argument is bool or string with 'true' or 'false' value.
    :param value: argument to check
    :return: True if argument is booleanlike, false if not
    """
    if isinstance(value, bool):
        return True
    if not isinstance(value, str):
        return False
    if value.lower() == "true" or value.lower() == "false":
        return True


def cast_bool(value) -> bool:
    """
    Tries to cast value to bool.
    Raises ValueError if value is ambiguous.
    Raises TypeError for unsupported types.
    :param value: value to cast
    :return: bool
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            raise ValueError("Ambiguous value of " + value)
    else:
        raise TypeError("Unsupported type of {} with value {}"
                        .format(type(value), value))


def swap_booleans(dictionary: dict, inplace: bool=True) -> dict:  # TODO: Extend functionality to lists too
    """
    Recursively iterates on dictionary and swaps booleanlike values with proper booleans.
    :param dictionary: input dictionary
    :param inplace: if True modifies inplace, if False creates deepcopy before changes
    :return: dictionary with swaped values
    """
    if not inplace:
        dictionary = copy.deepcopy(dictionary)
    for key in dictionary.keys():
        if isinstance(dictionary[key], dict):
            dictionary[key] = swap_booleans(dictionary[key], inplace=inplace)
        elif is_booleanlike(dictionary[key]):
            dictionary[key] = cast_bool(dictionary[key])
    return dictionary

if __name__ == '__main__':
    #  rudimentary test/proof of work
    dicto = load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    print(dicto)
    print(swap_booleans(dicto, False))
