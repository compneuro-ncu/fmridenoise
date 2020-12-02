from nipype import IdentityInterface
from itertools import chain


class FlattenIdentityInterface(IdentityInterface):
    """
    Identity interface that can also flatten some of it's fields before passing them forward
    """

    def __init__(self, fields, mandatory_inputs=True, flatten_fields=(), **inputs):
        super().__init__(fields=fields, mandatory_inputs=mandatory_inputs, **inputs)
        for flatten_field in flatten_fields:
            if flatten_field not in fields:
                raise RuntimeError(
                    f"Flatten fields have to be in fields, but field: {flatten_field} is missing in {fields}")
        self.flatten_fields = flatten_fields

    def _list_outputs(self):
        outputs = super()._list_outputs()
        for key in self.flatten_fields:
            outputs[key] = list(chain(*outputs[key]))
        return outputs
