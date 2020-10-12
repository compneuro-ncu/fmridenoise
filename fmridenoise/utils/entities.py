import typing as t
from bids.layout import parse_file_entities, writing
from fmridenoise.pipelines import extract_pipeline_from_path


def parse_file_entities_with_pipelines(filename, entities=None, config=None,
                                       include_unmatched=False) -> t.Dict[str, str]:
    et_dict = parse_file_entities(filename, entities, config, include_unmatched)
    et_dict['pipeline'] = extract_pipeline_from_path(filename)
    return et_dict


def build_path(entities, path_patterns, strict=False):
    path = writing.build_path(entities, path_patterns, strict)
    if path is not None:
        return path
    else:
        raise ValueError(f"Unable to build path with given entites: {entities}\n and path pattern {path_patterns}")
