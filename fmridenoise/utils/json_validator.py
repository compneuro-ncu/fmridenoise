import utils as ut
import jsonschema
import copy
pipeline_schema = {
    "type": "object",
    "required": ["name", "description", "confounds", "aroma", "spikes", "filter", "detrend", "standardize"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "confounds": {
            "type": "object",
            "required": ["wm", "csf", "gs", "motion", "acompcor"],
            "additionalProperties": False,
            "properties": {
                    "wm": {"type": "confound"},
                    "csf": {"type": "confound"},
                    "gs": {"type": "confound"},
                    "motion": {"type": "confound"},
                    "acompcor": {"type": "boolean"}
                }
            },
        "aroma": {"type": "boolean"},
        "spikes": {
            "type": "object",
            "required": ["fd_th", "dvars_th"],
            "additionalProperties": False,
            "properties": {
                "fd_th": {"type": "number"},
                "dvars_th": {"type": "number"}
            }
        },
        "filter": {
            "type": "object",
            "required": ["low_pass", "high_pass"],
            "additionalProperties": False,
            "properties": {
                "low_pass": {"type": "boolean"},
                "high_pass": {"type": "boolean"}
            }
        },
        "detrend": {"type":"boolean"},
        "standardize": {"type": "boolean"}
    }
}


def __is_confound(checker, instance) -> bool:
    if instance is False:
        return True
    elif isinstance(instance, dict):
        if tuple(instance.keys()) == ('temp_deriv', 'quad_terms'):
            if isinstance(instance['quad_terms'], bool) and isinstance(instance['temp_deriv'], bool):
                return True
            else:
                return False
        else:
            return False
    else:
        return False


__new_types = jsonschema.Draft7Validator.TYPE_CHECKER.redefine("confound", __is_confound)
__new_meta_schema = copy.deepcopy(jsonschema.Draft7Validator.META_SCHEMA)
__new_meta_schema['definitions']['simpleTypes']['enum'].append('confound')
__new_validator = jsonschema.Draft7Validator.VALIDATORS
PipelineValidator = jsonschema.validators.create(meta_schema=__new_meta_schema,
                                                 validators=__new_validator,
                                                 type_checker=__new_types)
__pipeline_validator = PipelineValidator(pipeline_schema)


def is_valid(pipeline: dict) -> bool:
    """
    Checks if pipeline is valid using PipelineValidator and pipeline_schema.
    :param pipeline: pipeline in jsonlike dictionary format
    :return: True if pipeline is valid, False if not
    """
    return __pipeline_validator.is_valid(instance=pipeline)


def validate(instance: dict, schema: dict=pipeline_schema, cls=PipelineValidator) -> None:
    """
    Validates jsonlike dictionary.
    Raises jsonschema.exceptions.ValidationError on failed validation.
    :param instance: json (as dictionary) to validate
    :param schema: schema used as validation template
    :param cls: Validator class used for validation
    :return: None
    """
    jsonschema.validate(instance, schema, cls)


validate.__doc__ = jsonschema.validators.validate.__doc__

if __name__ == '__main__':
    #rudimentary example/quickcheck of validity
    jdicto = ut.load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    validate(jdicto, pipeline_schema, cls=PipelineValidator) #  Better for standalone validation
    print(is_valid(jdicto))
