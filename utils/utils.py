import json
import jsonschema

_pipeline_valid_keys = ["name", "descrtiption", "confounds"]
type_checker = jsonschema.Draft4Validator.VALIDATORS


def load_pipeline_from_json(json_path: str) -> dict:
    with open(json_path, 'r') as json_file:
        js = json.load(json_file)  # ValueError if json_file is not a proper json file
    js = swap_booleans(js, inplace=True)
    return js


def is_boollike(string: str) -> bool:
    if isinstance(string, bool):
        return True
    if not isinstance(string, str):
        return False
    if string.lower() == "true" or string.lower() == "false":
        return True


def cast_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return True if value.lower() == 'true' else False
    else:
        raise TypeError("Unsupported type of {} with value {}"
                        .format(type(value), value))


def swap_booleans(dictionary: dict, inplace: bool=True) -> dict:
    if not inplace:
        dictionary = dictionary.copy()
    for key in dictionary.keys():
        if isinstance(dictionary[key], dict):
            dictionary[key] = swap_booleans(dictionary[key], inplace=inplace)
        elif is_boollike(dictionary[key]):
            dictionary[key] = cast_bool(dictionary[key])
    return dictionary


if __name__ == '__main__':
    #  rudimentary test/proof of work
    dicto = load_pipeline_from_json("../pipelines/36_parameters_spikes.json")
    print(dicto)
    print(swap_booleans(dicto, False))
