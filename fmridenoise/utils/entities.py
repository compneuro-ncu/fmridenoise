import typing as t
from bids.layout import parse_file_entities, writing
from fmridenoise.pipelines import extract_pipeline_from_path


def parse_file_entities_with_pipelines(filename, entities=None, config=None,
                                       include_unmatched=False) -> t.Dict[str, str]:
    """
    bids.extract_pipelines_from_path extended with ability to
    """
    et_dict = parse_file_entities(filename, entities, config, include_unmatched)
    pipeline = extract_pipeline_from_path(filename)
    if pipeline:
        et_dict['pipeline'] = pipeline
    return et_dict


def is_entity_subset(entity_superset: t.Dict[str, str], entity_subset: t.Dict[str, str]) -> bool:
    """
    Checks if all key values in subset are in superset
    Args:
        entity_superset: bigger dict
        entity_subset: smaller dict

    Returns: true if all key-values pairs from entity_subset are in entity_superset

    """
    return all(entity_superset.get(entity_key) == entity_value for entity_key, entity_value in entity_subset.items())


def build_path(entities, path_patterns, strict=False):
    """
    Extension of bids.build_path that throws exception instead of returning None
    Args:
        entities:
        A dictionary mapping entity names to entity values.
        Entities with ``None`` or empty-string value will be removed.
        Otherwise, entities will be cast to string values, therefore
        if any format is expected (e.g., zero-padded integers), the
        value should be formatted.
        path_patterns:
        A dictionary mapping entity names to entity values.
        Entities with ``None`` or empty-string value will be removed.
        Otherwise, entities will be cast to string values, therefore
        if any format is expected (e.g., zero-padded integers), the
        value should be formatted.
        strict:
        If True, all passed entities must be matched inside a
        pattern in order to be a valid match. If False, extra entities will
        be ignored so long as all mandatory entities are found.

    Returns: built path
    """
    path = writing.build_path(entities, path_patterns, strict)
    if path is not None:
        return path
    else:
        raise ValueError(f"Unable to build path with given entities: {entities}\n and path pattern {path_patterns}")


def assert_all_entities_equal(entities: t.List[t.Dict[str, str]], *entities_names: str) -> None:
    if len(entities) == 0:
        return
    for name in entities_names:
        first = entities[0].get(name)
        if any(entity.get(name) != first for entity in entities):
            raise AssertionError(f"Not all entities equal for key: {name}\n"
                                 f"{[entitie.get(name) for entitie in entities]}")
