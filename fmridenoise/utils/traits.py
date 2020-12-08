import typing as t
from traits.trait_types import Union, TraitType, Instance
from traits.trait_base import _Undefined, Undefined


def Optional(trait: TraitType) -> Union:
    """
    Return Union of function argument and Instance(_Undefined)
    Args:
        trait (TraitType): optional trait

    Returns:
        union with undefined instance

    """
    return Union(trait, Instance(_Undefined))


def remove_undefined(iterable: t.Iterable) -> t.Iterable:
    """
    Creates generator that ignores all instances of _Undefined
    Args:
        iterable (Iterable): objects iterable

    Returns:
        generator
    """
    return (element for element in iterable if element is not Undefined)
