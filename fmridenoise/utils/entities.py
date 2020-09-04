import typing as t
from bids.layout import  parse_file_entities
from fmridenoise.pipelines import extract_pipeline_from_path


def parse_file_entities_with_pipelines(filename, entities=None, config=None,
                                       include_unmatched=False) -> t.Dict[str, str]:
    et_dict = parse_file_entities(filename, entities, config, include_unmatched)
    et_dict['pipeline'] = extract_pipeline_from_path(filename)
    return et_dict
