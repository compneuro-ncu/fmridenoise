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
from os.path import join
from itertools import chain

import seaborn as sns
sns.set()


class QualityMeasuresInputSpec(BaseInterfaceInputSpec):
    group_corr_mat = File(exists=True,
                          desc='Group connectivity matrix',
                          mandatory=True)

    group_conf_summary = File(exists=True,
                              desc='Group confounds summmary',
                              mandatory=True)

    distance_matrix = File(exists=True,
                           desc='Distance matrix',
                           mandatory=True)

    output_dir = File(desc='Output path')
    pipeline_name = traits.Str(mandatory=True)


class QualityMeasuresOutputSpec(TraitedSpec):
    fc_fd_summary = traits.List(
        exists=True,
        desc="QC-FC quality measures")
    edges_weight = traits.List(
        exists=True,
        desc="Weights of individual edges")


class QualityMeasures(SimpleInterface):
    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        # Loading data
        group_corr_mat = np.load(self.inputs.group_corr_mat)
        group_conf_summary = pd.read_csv(self.inputs.group_conf_summary, sep='\t')
        pipeline_name = self.inputs.pipeline_name
        distance_vector = sym_matrix_to_vec(np.load(self.inputs.distance_matrix))

        # Creating vectors with subject filter
        all_sub_no = len(group_conf_summary)
        icluded_sub = group_conf_summary["include"]
        excluded_sub_no = all_sub_no - sum(icluded_sub)

        included = {f"All subjects (n = {all_sub_no})":
                        [np.ones((all_sub_no), dtype=bool), False, all_sub_no, "raw"],
                    f"After excluding {excluded_sub_no} high motion subjects (n = {all_sub_no - excluded_sub_no})":
                        [group_conf_summary["include"].values.astype("bool"), True, all_sub_no - excluded_sub_no,
                         "cleaned"]
                    }

        group_corr_vec = sym_matrix_to_vec(group_corr_mat)
        n_edges = group_corr_vec.shape[1]

        fc_fd_corr, fc_fd_pval = (np.zeros(n_edges) for _ in range(2))
        fc_fd_summary, edges_weight = ([] for _ in range(2))

        for key, value in included.items():

            for i in range(n_edges):
                corr = pearsonr(group_corr_vec[value[0], i], group_conf_summary['mean_fd'].values[value[0]])
                fc_fd_corr[i] = corr[0]
                fc_fd_pval[i] = corr[1]

            fc_fd_corr = np.nan_to_num(fc_fd_corr)  # TODO: write exception

            distance_dependence = pearsonr(fc_fd_corr, distance_vector)[0]

            fc_fd_summary.append({"pipeline": pipeline_name,
                                  "perc_fc_fd_uncorr": np.sum(fc_fd_pval < 0.5) / len(fc_fd_pval) * 100,
                                  "pearson_fc_fd": np.median(fc_fd_corr),
                                  "distance_dependence": distance_dependence,
                                  "tdof_loss": group_conf_summary["n_conf"].mean(),
                                  "cleaned": value[1],
                                  "sub_no": value[2]
                                  })

            edges_weight.append({pipeline_name: group_corr_vec.mean(axis=0),
                                 "cleaned": value[1],
                                 "sub_no": value[2]})

            # --- plotting matrices
            vec = vec_to_sym_matrix(fc_fd_corr)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            fig1 = ax1.imshow(group_corr_mat.mean(axis=0), vmin=-1, vmax=1, cmap="RdBu_r")
            ax1.set_title(f"{pipeline_name}: mean FC")
            fig.colorbar(fig1, ax=ax1)

            fig2 = ax2.imshow(vec, vmin=-1, vmax=1, cmap="RdBu_r")
            ax2.set_title(f"{pipeline_name}: FC-FD correlation")
            fig.colorbar(fig2, ax=ax2)
            fig.suptitle(f"{pipeline_name}: {key}")

            fig.savefig(join(self.inputs.output_dir, f"FC_FD_corr_mat_{pipeline_name}_{value[3]}.png"),
                        dpi=300)  # TODO self

            self._results["fc_fd_summary"] = fc_fd_summary
            self._results["edges_weight"] = edges_weight



        # group_corr_vec = sym_matrix_to_vec(group_corr_mat)
        #
        # n_edges = group_corr_vec.shape[1]
        # fc_fd_corr = np.zeros(n_edges)
        # fc_fd_pval = np.zeros(n_edges)
        #
        # for i in range(n_edges):
        #     corr = pearsonr(group_corr_vec[:, i], group_conf_summary['mean_fd'].values)
        #     fc_fd_corr[i] = corr[0]
        #     fc_fd_pval[i] = corr[1]
        #
        # distance_dependence = pearsonr(fc_fd_corr, distance_vector)[0]
        #
        # fc_fd_summary = {"pipeline": pipeline_name,
        #                  "perc_fc_fd_uncorr": np.sum(fc_fd_pval < 0.5)/len(fc_fd_pval)*100,
        #                  "pearson_fc_fd": np.median(fc_fd_corr),
        #                  "distance_dependence": distance_dependence,
        #                  "tdof_loss": group_conf_summary["n_conf"].mean(),
        #                  }
        #
        # edges_weight = {pipeline_name: group_corr_vec.mean(axis=0)}
        #
        # # --- plotting matrices
        # vec = vec_to_sym_matrix(fc_fd_corr)
        # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        #
        # fig1 = ax1.imshow(group_corr_mat.mean(axis=0), vmin=-1, vmax=1, cmap="RdBu_r")
        # ax1.set_title(f"{pipeline_name}: mean FC")
        # fig.colorbar(fig1, ax=ax1)
        #
        # fig2 = ax2.imshow(vec, vmin=-1, vmax=1, cmap="RdBu_r")
        # ax2.set_title(f"{pipeline_name}: FC-FD correlation")
        # fig.colorbar(fig2, ax=ax2)
        #
        # fig.savefig(join(self.inputs.output_dir, f"FC_FD_corr_mat_{pipeline_name}.png"), dpi=300)
        #
        # self._results["fc_fd_summary"] = fc_fd_summary
        # self._results["edges_weight"] = edges_weight


        return runtime


class MergeGroupQualityMeasuresOutputSpec(TraitedSpec):
        fc_fd_summary = traits.List()
        edges_weight = traits.List()


class MergeGroupQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List()
    edges_weight = traits.List()


class MergeGroupQualityMeasures(SimpleInterface):
    input_spec = MergeGroupQualityMeasuresInputSpec
    output_spec = MergeGroupQualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        self._results['fc_fd_summary'] = self.inputs.fc_fd_summary
        self._results['edges_weight'] = self.inputs.edges_weight
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

        pipelines_fc_fd_summary = pd.DataFrame(list(chain.from_iterable(self.inputs.fc_fd_summary[0]))) #pd.DataFrame()
        pipelines_edges_weight = pd.DataFrame(list(chain.from_iterable(self.inputs.edges_weight[0]))) #pd.DataFrame()

        # for summary, edges in zip(self.inputs.fc_fd_summary, self.inputs.edges_weight):
        #
        #     pipelines_fc_fd_summary = pd.concat([pipelines_fc_fd_summary, pd.DataFrame([summary[0]])], axis=0)
        #     pipelines_edges_weight = pd.concat([pipelines_edges_weight, pd.DataFrame(edges[0])], axis=1)


        fname1 = join(self.inputs.output_dir, f"pipelines_fc_fd_summary.tsv")
        fname2 = join(self.inputs.output_dir, f"pipelines_edges_weight.tsv")

        pipelines_fc_fd_summary.to_csv(fname1, sep='\t', index=False)
        pipelines_edges_weight.to_csv(fname2, sep='\t', index=False)

        # --- Plotting

        # density plot
        fig1, ax = plt.subplots(1, 1)

        for col in pipelines_edges_weight:
            sns.kdeplot(pipelines_edges_weight[col], shade=True)
            plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
            plt.title("Density of edge weights")

        fig1.savefig(f"{self.inputs.output_dir}/pipelines_edges_density.svg", dpi=300)

        # boxplot (Pearson's r FC-DC)
        fig2, ax = plt.subplots(1, 1)
        sns.barplot(x="pearson_fc_fd",
                    y="pipeline",
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC (Pearson's r)",
                                    ylabel='Pipeline')
        fig2.savefig(f"{self.inputs.output_dir}/pipelines_fc_fd_pearson.svg", dpi=300, bbox_inches="tight")

        # boxplot (% correlated edges)
        fig3, ax = plt.subplots(1, 1)
        sns.barplot(x="perc_fc_fd_uncorr",
                    y="pipeline",
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC uncorrected (%)",
                                    ylabel='Pipeline')

        fig3.savefig(f"{self.inputs.output_dir}/pipelines_fc_fd_uncorr.svg", dpi=300, bbox_inches="tight")

        # boxplot (Pearson's r FC-DC with distance)

        fig4, ax = plt.subplots(1, 1)
        sns.barplot(x="distance_dependence",
                    y="pipeline",
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="Distance-dependence",
                                    ylabel='Pipeline')
        fig4.savefig(f"{self.inputs.output_dir}/pipelines_distance_dependence.svg", dpi=300, bbox_inches="tight")



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