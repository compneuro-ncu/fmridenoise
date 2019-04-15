from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

import nibabel as nb
import numpy as np
import os

class BasicDenoisingInterfaceInputSpec(BaseInterfaceInputSpec):
    confounds = File(exists=True, desc='confounds file', mandatory=True)
    strategy = File(exists=True, desc='denoising strategy to apply', mandatory=True)
    # threshold = traits.Float(desc='everything below this value will be set to zero',
    #                          mandatory=True)


class BasicdenoisingInterfaceOutputSpec(TraitedSpec):
    ...
    #thresholded_volume = File(exists=True, desc="thresholded volume")


class SimpleThreshold(BaseInterface):
    input_spec = BasicDenoisingInterfaceInputSpec
    output_spec = BasicdenoisingInterfaceOutputSpec

    def _run_interface(self, runtime):
        """
        Calls denoising function with appropriate strategy.
        Musi ręcznie zapisać pliki, które mają być potem używane do daleszej analizy.
        :param runtime:
        :return:
        """
        # fname = self.inputs.volume
        # img = nb.load(fname)
        # data = np.array(img.get_data())
        #
        # active_map = data > self.inputs.threshold
        #
        # thresholded_map = np.zeros(data.shape)
        # thresholded_map[active_map] = data[active_map]
        #
        # new_img = nb.Nifti1Image(thresholded_map, img.affine, img.header)
        # _, base, _ = split_filename(fname)
        # nb.save(new_img, base + '_thresholded.nii')

        return runtime

    # def _list_outputs(self):
    #     outputs = self._outputs().get()
    #     fname = self.inputs.volume
    #     _, base, _ = split_filename(fname)
    #     outputs["thresholded_volume"] = os.path.abspath(base + '_thresholded.nii')
    #     return outputs
