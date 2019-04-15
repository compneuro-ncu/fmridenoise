import os
from pathlib import Path
from gzip import GzipFile
import json
import shutil
import numpy as np
import nibabel as nb

from nipype import logging
from nipype.utils.filemanip import makedirs, copyfile
from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )
from nipype.interfaces.io import IOBase


class LoadBIDSDenoisingInputSpec(BaseInterfaceInputSpec):
    bids_dir = Directory(exists=True,
                         mandatory=True,
                         desc='BIDS dataset root directory')
    derivatives = traits.Either(traits.Bool,
                                InputMultiPath(Directory(exists=True)),
                                desc='Derivative folders')
    electors = traits.Dict(desc='Limit collected sessions', usedefault=True)
    force_index = InputMultiPath(
        traits.Str,
        desc='Patterns to select sub-directories of BIDS root')
    ignore = InputMultiPath(
        traits.Str,
        desc='Patterns to ignore sub-directories of BIDS root')

class LoadBIDSDenoisingOutputSpec(BaseInterfaceInputSpec):
    pass
