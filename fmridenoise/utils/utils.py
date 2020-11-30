import copy
from os.path import join

from nipype import Node, JoinNode, IdentityInterface
import typing as t
import os
import shutil
from fmridenoise.interfaces.utility import FlattenIdentityInterface
from fmridenoise._version import get_versions


def create_dataset_description_json_content() -> str:
    directory_name = os.path.dirname(__file__)
    with open(join(directory_name, "dataset_description_template.json"), "r") as template_f:
        template = str(template_f.read())
    get_versions_result = get_versions()
    version = get_versions_result['version']
    main_url_template = "https://github.com/compneuro-ncu/fmridenoise/releases/tag/{ver}"
    code_url = "NO URL, DEVELOPMENT BUILD" if any(
        map(version.__contains__, ["+", "dirty"])) else main_url_template.format(ver=version)
    return template.replace("{fmridenoise_version}", version).replace("{fmridenoise_codeurl}", code_url)


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


def swap_booleans(dictionary: dict, inplace: bool = True) -> dict:  # TODO: Extend functionality to lists too
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


def create_identity_join_node(name: str, fields: t.List[str], joinsource: t.Union[Node, str]) -> JoinNode:
    return JoinNode(IdentityInterface(fields=fields), name=name, joinsource=joinsource, joinfield=fields)


def create_flatten_identity_join_node(name: str, fields: t.List[str],
                                      joinsource: t.Union[Node, str], flatten_fields: t.List[str]) -> JoinNode:
    return JoinNode(FlattenIdentityInterface(fields=fields, flatten_fields=flatten_fields),
                    name=name, joinsource=joinsource, joinfield=fields)


def copy_as_dummy_dataset(source_bids_dir: str, new_path: str, ext_to_copy=tuple()) -> None:
    """
    Walks trough BIDS dataset and recreates it's structure but with
    empty files.

    Arguments:
        source_bids_dir {str} -- source of BIDS dataset
        new_path {str} -- destination of new dummy_complete dataset

    Keyword Arguments:
        ext_to_copy {tuple or str} -- files with given extensions
        will be copied instead of empty (default: {tuple()})

    Returns:
        None
    """

    if type(ext_to_copy) is str:
        ext_to_copy = (ext_to_copy,)
    source_bids_dir = os.path.abspath(source_bids_dir)
    if not os.path.isdir(new_path):
        os.makedirs(new_path)
    for root, dirs, files in os.walk(source_bids_dir, topdown=True):
        rel_root = os.path.relpath(root, source_bids_dir)
        rel_root = rel_root.strip(".")
        rel_root = rel_root.strip("/")
        new_root = os.path.join(new_path, rel_root)
        for name in dirs:
            os.makedirs(os.path.join(new_root, name))
        for name in files:
            for ext in ext_to_copy:
                if str(name).endswith(ext):
                    shutil.copy2(os.path.join(root, name), os.path.join(new_root, name))
                    break
            else:
                open(os.path.join(new_root, name), 'w').close()
