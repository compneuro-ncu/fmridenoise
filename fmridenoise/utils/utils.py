import copy
from nipype import Node, JoinNode, IdentityInterface
import typing as t

from fmridenoise.interfaces.utility import FlattenIdentityInterface


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


def create_identity_join_node(name: str, fields: t.List[str], joinsource: t.Union[Node, str]) -> JoinNode:
    return JoinNode(IdentityInterface(fields=fields), name=name, joinsource=joinsource, joinfield=fields)


def create_flatten_identity_join_node(name: str, fields: t.List[str],
                                      joinsource: t.Union[Node, str], flatten_fields: t.List[str]) -> JoinNode:
    return JoinNode(FlattenIdentityInterface(fields=fields, flatten_fields=flatten_fields),
                    name=name, joinsource=joinsource, joinfield=fields)
