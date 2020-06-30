import jsonschema

confound_schema = {
    'type': 'object',
    'properties': {
        'raw': {'type': 'boolean'},
        'derivative1': {'type': 'boolean'},
        'power2': {'type': 'boolean'},
        'derivative1_power2': {'type': 'boolean'},
        },
    'required': ['raw', 'derivative1', 'power2', 'derivative1_power2'],
    'additionalProperties': False
}

spike_schema = {
    'anyOf': [
        {'enum': [ False ]},
        {
            'type': 'object',
            'properties': {
                'fd_th': {'type': 'number', 'minimum': 0},
                'dvars_th': {'type': 'number', 'minimum': 0}
            },
        'required': ['fd_th', 'dvars_th'],
        'additionalProperties': False
        }        
    ]
}

pipeline_schema = {
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string',
            'minLength': 1
            },
        'description': {'type': 'string'}, 
        'confounds': {
            'type': 'object',
            'properties': {
                'white_matter': confound_schema,
                'csf': confound_schema,    
                'global_signal': confound_schema,
                'motion': confound_schema,
                'acompcor': {'type': 'boolean'}
                },
            'required': ['white_matter', 'csf', 'global_signal', 'motion', 'acompcor'],
            'additionalProperties': False
            },
        'aroma': {'type': 'boolean'},
        'spikes': spike_schema
        },
    'required': ['name', 'confounds', 'aroma', 'spikes'],
    'additionalProperties': False
}


def validate(pipeline: dict) -> None:
    '''Checks if denoising pipeline is valied.
    
    Checks if pipeline dictionary conforms to denoising pipeline schema. 
    Denoising pipeline unambigously defines denoising strategy.

    Args:
        pipeline: Denoising pipeline dictionary.

    Returns:
        None if pipeline is valid.

    Raises:
        ValidationError or SchemaError if pipeline is not valid.
    '''
    jsonschema.validate(instance=pipeline, schema=pipeline_schema)


def is_valid(pipeline: dict, silent=False) -> bool:
    '''Returns decision if denoising pipeline is valid.
    
    Args:
        pipeline: 
            Denoising pipeline dictionary.
        silent (default False): 
            If silent is True, errors won't be printed to the console.
    '''
    if not isinstance(pipeline, dict):
        raise TypeError('pipeline should be dictionary')
    
    validator = jsonschema.Draft7Validator(pipeline_schema)
    
    if validator.is_valid(pipeline):
        return True
    else:
        if not silent:
            for error in validator.iter_errors(pipeline):
                print(40 * '-' + '\n', error)
        return False
