import typing as t
from collections import namedtuple

from bids.layout import parse_file_entities
from bids.layout import parse_file_entities, writing

from fmridenoise.pipelines import extract_pipeline_from_path


def parse_file_entities_with_pipelines(filename, entities=None, config=None,
                                       include_unmatched=False) -> t.Dict[str, str]:
    et_dict = parse_file_entities(filename, entities, config, include_unmatched)
    et_dict['pipeline'] = extract_pipeline_from_path(filename)
    return et_dict


def entity_tuple_from_dict(entity_dict):
    EntityTuple = namedtuple('EntityTuple', 'task session')

    if 'session' in entity_dict:
        return EntityTuple(entity_dict['task'], entity_dict['session'])
    else:
        return EntityTuple(entity_dict['task'], None)


def entity_tuple_to_entity_name(entity_tuple):
    '''Converts into name of task / task+session entity used for the report 
    tab title.'''
    if entity_tuple.session is None:
        return f'task-{entity_tuple.task}'
    else:
        return f'task-{entity_tuple.task} ses-{entity_tuple.session}'


def entity_tuple_to_entity_id(entity_tuple):
    '''Converts into id of task / task+session entity used for html elements 
    id.'''
    if entity_tuple.session is None:
        return f'task-{entity_tuple.task}'
    else:
        return f'task-{entity_tuple.task}-ses-{entity_tuple.session}'


def entity_match_path(entity_tuple, path):
    '''
    Input:
        entity_tuple (EntityTuple):
        path (str):
    Returns:
        bool
    '''
    entity_dict = parse_file_entities_with_pipelines(path)
    return entity_tuple_from_dict(entity_dict) == entity_tuple


def build_path(entities, path_patterns, strict=False):
    path = writing.build_path(entities, path_patterns, strict)
    if path is not None:
        return path
    else:
        raise ValueError(f"Unable to build path with given entites: {entities}\n and path pattern {path_patterns}")

