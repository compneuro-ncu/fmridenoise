from nipype.interfaces.base import (
    BaseInterfaceInputSpec, TraitedSpec, SimpleInterface,
    InputMultiPath, OutputMultiPath, File, Directory,
    traits, isdefined
    )

import numpy as np
import pandas as pd
from nilearn.connectome import sym_matrix_to_vec, vec_to_sym_matrix
from scipy.stats import pearsonr
import matplotlib.pyplot as plt


class QualityMeasuresInputSpec(BaseInterfaceInputSpec):
    group_corr_mat = File(exists=True,
                          desc='Group connectivity matrix',
                          mandatory=True)

    group_conf_summary = File(exists=True,
                              desc='Group confounds summmary',
                              mandatory=True)

    output_dir = File(desc='Output path')
    pipeline_name = traits.Str(mandatory=True)


class QualityMeasuresOutputSpec(TraitedSpec):
    fc_fd_summary = traits.Dict(
        exists=True,
        desc="QC-FC quality measures")
    edges_weight = traits.Dict(
        exists=True,
        desc="Weights of individual edges")


class QualityMeasures(SimpleInterface):
    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        group_corr_mat = np.load(self.inputs.group_corr_mat)
        group_conf_summary = pd.read_csv(self.inputs.group_conf_summary, sep='\t')
        pipeline_name = self.inputs.pipeline_name

        vectorized = sym_matrix_to_vec(group_corr_mat)

        n_edges = vectorized.shape[1]
        fc_fd_corr = np.zeros(n_edges)
        fc_fd_pval = np.zeros(n_edges)

        for i in range(n_edges):
            corr = pearsonr(vectorized[:, i], group_conf_summary['mean_fd'].values)
            fc_fd_corr[i] = corr[0]
            fc_fd_pval[i] = corr[1]

        fc_fd_summary = {"pipeline": pipeline_name,
                         "perc_fc_fd_uncorr": np.sum(fc_fd_pval < 0.5)/len(fc_fd_pval)*100,
                         "pearson_fc_fd": np.median(fc_fd_corr),
                         "tdof_loss": group_conf_summary["n_conf"].mean()
                         }

        edges_weight = {pipeline_name: vectorized.mean(axis=0)}

        fc_fd_summary_df = pd.DataFrame([fc_fd_summary])
        edges_weight_df = pd.DataFrame(edges_weight)

        fc_fd_summary_df.to_csv(f"{self.inputs.output_dir}fc_fd_summary_{pipeline_name}.tsv", sep='\t', index=False)
        edges_weight_df.to_csv(f"{self.inputs.output_dir}edges_weight_{pipeline_name}.tsv", sep='\t', index=False)

        # --- plotting matrices
        vec = vec_to_sym_matrix(fc_fd_corr)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        fig1 = ax1.imshow(group_corr_mat.mean(axis=0), vmin=-1, vmax=1, cmap="RdBu_r")
        ax1.set_title(f"{pipeline_name}: mean FC")
        fig.colorbar(fig1, ax=ax1)

        fig2 = ax2.imshow(vec, vmin=-1, vmax=1, cmap="RdBu_r")
        ax2.set_title(f"{pipeline_name}: FC-FD correlation")
        fig.colorbar(fig2, ax=ax2)

        fig.savefig(f"{self.inputs.output_dir}FC_FD_corr_mat_{pipeline_name}.png", dpi=300)

        self._results["fc_fd_summary"] = fc_fd_summary
        self._results["edges_weight"] = edges_weight


        return runtime


class PipelinesQualityMeasuresInputSpec(BaseInterfaceInputSpec):

    fc_fd_summary = traits.List(
        exists=True,
        desc="QC-FC quality measures")
    edges_weight = traits.List(
        exists=True,
        desc="Weights of individual edges")
    output_dir = File(          # needed to save data in other directory
        desc="Output path")     # TODO: Implement temp dir


class PipelinesQualityMeasuresOutputSpec(TraitedSpec):

    pipelines_fc_fd_summary = File(
        exists=True,
        desc="Group QC-FC quality measures")
    pipelines_edges_weight = File(
        exists=True,
        desc="Group weights of individual edges")


class PipelinesQualityMeasures(SimpleInterface):
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        pipelines_fc_fd_summary = pd.DataFrame()
        pipelines_edges_weight = pd.DataFrame()

        for summary, edges in zip(self.inputs.fc_fd_summary, self.inputs.edges_weight):

            pipelines_fc_fd_summary = pd.concat([pipelines_fc_fd_summary, pd.DataFrame([summary])], axis=0)
            pipelines_edges_weight = pd.concat([pipelines_edges_weight, pd.DataFrame(edges)], axis=1)


        fname1 = f"{self.inputs.output_dir}pipelines_fc_fd_summary.tsv"
        fname2 = f"{self.inputs.output_dir}pipelines_edges_weight.tsv"

        pipelines_fc_fd_summary.to_csv(fname1, sep='\t', index=False)
        pipelines_edges_weight.to_csv(fname2, sep='\t', index=False)

        self._results['pipelines_fc_fd_summary'] = fname1
        self._results['pipelines_edges_weight'] = fname2

        return runtime



# --- TESTING

if __name__ == '__main__':

    qc = QualityMeasures()

    qc.inputs.group_conf_summary = '/media/finc/Elements/BIDS_pseudowords/BIDS/derivatives/fmridenoise/36_parameters_spikes_group_conf_summary.tsv'
    qc.inputs.group_corr_mat = '/media/finc/Elements/BIDS_pseudowords/BIDS/derivatives/fmridenoise/36_parameters_spikes_group_corr_mat.npy'
    qc.inputs.output_dir = "/home/finc/"
    qc.inputs.pipeline_name = "test"

    results = qc.run()
    print(results.outputs)