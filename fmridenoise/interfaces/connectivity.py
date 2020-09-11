import numpy as np
from bids.layout import parse_file_entities
from bids.layout.writing import build_path

from nipype.interfaces.base import (BaseInterfaceInputSpec, TraitedSpec,
                                    SimpleInterface, File, Directory,
                                    traits)
import nibabel as nb
from nilearn.input_data import NiftiLabelsMasker
from nilearn.connectome import ConnectivityMeasure

from fmridenoise.parcellation import get_parcellation_file_path
from fmridenoise.pipelines import extract_pipeline_from_path
from fmridenoise.utils.quality_measures import create_carpetplot
from nilearn.plotting import plot_matrix
from os.path import join


class ConnectivityInputSpec(BaseInterfaceInputSpec):
    fmri_denoised = File(
        exists=True,
        desc='Denoised fMRI file',
        mandatory=True)
    output_dir = Directory(
        exists=True,
        desc='Output path')


class ConnectivityOutputSpec(TraitedSpec):
    corr_mat = File(
        exists=True,
        desc='Connectivity matrix',
        mandatory=True)
    carpet_plot = File(
        exists=True,
        desc='Carpet plot',
        mandatory=True)
    matrix_plot = File(
        exists=True,
        desc='Carpet plot',
        mandatory=True)


class Connectivity(SimpleInterface):
    input_spec = ConnectivityInputSpec
    output_spec = ConnectivityOutputSpec
    conn_file_pattern = "sub-{subject}[_ses_{session}]_task-{task}_pipeline-{pipeline}_connMat.npy"
    carpet_plot_pattern = "sub-{subject}[_ses_{session}]_task-{task}_pipeline-{pipeline}_carpetPlot.png"
    matrix_plot_pattern = "sub-{subject}[_ses_{session}]_task-{task}_pipeline-{pipeline}_matrixPlot.png"

    def _run_interface(self, runtime):
        fname = self.inputs.fmri_denoised
        entities = parse_file_entities(fname)
        bold_img = nb.load(fname)
        parcellation_file = get_parcellation_file_path(entities['space'])
        masker = NiftiLabelsMasker(labels_img=parcellation_file, standardize=True)
        time_series = masker.fit_transform(bold_img, confounds=None)

        corr_measure = ConnectivityMeasure(kind='correlation')
        corr_mat = corr_measure.fit_transform([time_series])[0]
        entities['pipeline'] = extract_pipeline_from_path(fname)
        conn_file = join(self.inputs.output_dir, build_path(entities, self.conn_file_pattern, False))
        carpet_plot_file = join(self.inputs.output_dir, build_path(entities, self.carpet_plot_pattern, False))
        matrix_plot_file = join(self.inputs.output_dir, build_path(entities, self.matrix_plot_pattern, False))

        create_carpetplot(time_series, carpet_plot_file)
        mplot = plot_matrix(corr_mat,  vmin=-1, vmax=1)
        mplot.figure.savefig(matrix_plot_file)

        np.save(conn_file, corr_mat)

        self._results['corr_mat'] = conn_file
        self._results['carpet_plot'] = carpet_plot_file
        self._results['matrix_plot'] = matrix_plot_file

        return runtime


class GroupConnectivityInputSpec(BaseInterfaceInputSpec):
    corr_mat = traits.List(
        File(exists=True),
        mandatory=True,
        desc='Connectivity matrix file')

    output_dir = Directory(
        exists=True,
        mandatory=True,
        desc='Output path')
    pipeline_name = traits.Str(
        mandatory=True,
        desc="Pipeline name")
    session = traits.Str(
        mandatory=False,
        desc="Session name")
    task = traits.Str(
        mandatory=True,
        desc="Task name")


class GroupConnectivityOutputSpec(TraitedSpec):
    group_corr_mat = File(
        exists=True,
        desc='Connectivity matrix',
        mandatory=True)


class GroupConnectivity(SimpleInterface):
    input_spec = GroupConnectivityInputSpec
    output_spec = GroupConnectivityOutputSpec
    group_corr_pattern = "[ses-{session}_]task-{task}_pipeline-{pipeline}_groupCorrMat.npy"

    def _run_interface(self, runtime):
        n_corr_mat = len(self.inputs.corr_mat)
        n_rois = 200
        group_corr_mat = np.zeros((n_corr_mat, n_rois, n_rois))
        for i, file in enumerate(self.inputs.corr_mat):
            group_corr_mat[i, :, :] = np.load(file)
        entities = {
            'pipeline': self.inputs.pipeline_name,
            'task': self.inputs.task
        }
        if self.inputs.session:
            entities['session'] = self.inputs.session
        group_corr_file = join(self.inputs.output_dir, build_path(entities, self.group_corr_pattern, False))
        np.save(group_corr_file, group_corr_mat)

        self._results['group_corr_mat'] = group_corr_file
        return runtime
