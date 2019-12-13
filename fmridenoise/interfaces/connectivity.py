import numpy as np

from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )
from nipype.utils.filemanip import split_filename
import nibabel as nb
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure
from fmridenoise.utils.quality_measures import create_carpetplot
from nilearn.plotting import plot_matrix
from os.path import join
class ConnectivityInputSpec(BaseInterfaceInputSpec):
    fmri_denoised = File(exists=True,
                         desc='Denoised fMRI file',
                         mandatory=True)
    parcellation = File(exists=True,
                        desc='Parcellation file',
                        mandatory=True)
    output_dir = File(desc='Output path')


class ConnectivityOutputSpec(TraitedSpec):
    corr_mat = File(exists=True,
                    desc='Connectivity matrix',
                    mandatory=True)
    carpet_plot = File(exists=True,
                    desc='Carpet plot',
                    mandatory=True)
    matrix_plot = File(exists=True,
                    desc='Carpet plot',
                    mandatory=True)


class Connectivity(SimpleInterface):
    input_spec = ConnectivityInputSpec
    output_spec = ConnectivityOutputSpec

    def _run_interface(self, runtime):
        fname = self.inputs.fmri_denoised
        bold_img = nb.load(fname)
        masker = NiftiLabelsMasker(labels_img=self.inputs.parcellation, standardize=True)
        time_series = masker.fit_transform(bold_img, confounds=None)

        corr_measure = ConnectivityMeasure(kind='correlation')
        corr_mat = corr_measure.fit_transform([time_series])[0]
        _, base, _ = split_filename(fname)

        conn_file = f'{self.inputs.output_dir}/{base}_conn_mat.npy'

        carpet_plot_file = join(self.inputs.output_dir, f'{base}_carpet_plot.png')
        matrix_plot_file = join(self.inputs.output_dir, f'{base}_matrix_plot.png')

        create_carpetplot(time_series, carpet_plot_file)
        mplot = plot_matrix(corr_mat,  vmin=-1, vmax=1)
        mplot.figure.savefig(matrix_plot_file)

        np.save(conn_file, corr_mat)

        self._results['corr_mat'] = conn_file
        self._results['carpet_plot'] = carpet_plot_file
        self._results['matrix_plot'] = matrix_plot_file

        return runtime


class GroupConnectivityInputSpec(BaseInterfaceInputSpec):
    corr_mat = traits.List(exists=True,
                    desc='Connectivity matrix',
                    mandatory=True)

    output_dir = File(desc='Output path')
    pipeline_name = traits.Any(mandatory=True) # FIXME



class GroupConnectivityOutputSpec(TraitedSpec):
    group_corr_mat = File(exists=True,
                    desc='Connectivity matrix',
                    mandatory=True)


class GroupConnectivity(SimpleInterface):
    input_spec = GroupConnectivityInputSpec
    output_spec = GroupConnectivityOutputSpec

    def _run_interface(self, runtime):
        n_corr_mat = len(self.inputs.corr_mat)
        n_rois = 200
        group_corr_mat = np.zeros((n_corr_mat, n_rois, n_rois))
        for i, file in enumerate(self.inputs.corr_mat):
            group_corr_mat[i, :, :] = np.load(file)

        pipeline_name = self.inputs.pipeline_name

        group_corr_file = join(self.inputs.output_dir, f'{pipeline_name}_group_corr_mat.npy')
        np.save(group_corr_file, group_corr_mat)

        self._results['group_corr_mat'] = group_corr_file
        # self._results['pipeline_name'] = pipeline_name

        return runtime
