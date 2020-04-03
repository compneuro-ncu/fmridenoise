import json
import copy
from os.path import exists
import re
# _pipeline_valid_keys = ["name", "descrtiption", "confounds"]


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


def split_suffix(basename):
    """
    Takes bids dataset filename and splits it into suffix and rest of file basename.
    Args:
        basename: bids file basename.

    Returns:
       basename without suffix
       suffix
    """
    match = re.search("([a-z 0-9 A-Z]{1,}\\-{1}[a-z 0-9 A-Z]{1,}_{0,}){1,}", basename)
    if match:
        return basename[match.regs[0][0]:match.regs[0][1]].strip('_'), basename[match.regs[0][1]:].strip('_')
    else:
        return basename, ""


if __name__ == '__main__':
     basename = "pipeline-24HMP8PhysSpikeReg_sub-m03_task-prlpun_space-MNI152NLin2009cAsym_desc-preproc_boldSmoothedDenoised_carpet_plot"
     # basename = "dupa"
     print(split_suffix(basename))