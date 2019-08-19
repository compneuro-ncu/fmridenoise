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

    edges_weight = traits.Dict(
        exists=True,
        desc="Weights of individual edges")

    edges_weight_clean = traits.Dict(
        exists=True,
        desc="Weights of individual edges after "
             "removing subjects with high motion")


class QualityMeasures(SimpleInterface):
    input_spec = QualityMeasuresInputSpec
    output_spec = QualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        # Loading data
        group_corr_mat = np.load(self.inputs.group_corr_mat)  # array with matrices for all runs
        group_conf_summary = pd.read_csv(self.inputs.group_conf_summary, sep='\t')  # motion summary for all runs
        pipeline_name = self.inputs.pipeline_name
        distance_vector = sym_matrix_to_vec(np.load(self.inputs.distance_matrix))  # load distance matrix

        # Creating vectors with subject filter
        all_sub_no = len(group_conf_summary)
        icluded_sub = group_conf_summary["include"]
        excluded_sub_no = all_sub_no - sum(icluded_sub) # number of subjects excluded from analyses

        # Create dictionary describing full sampple and sample after exluding highly motion runs
        included = {f"All subjects (n = {all_sub_no})":
                        [np.ones((all_sub_no), dtype=bool), False, all_sub_no, "All"],
                    f"After excluding {excluded_sub_no} high motion subjects (n = {all_sub_no - excluded_sub_no})":
                        [group_conf_summary["include"].values.astype("bool"), True, all_sub_no - excluded_sub_no,
                         "No_high_motion"]
                    }

        group_corr_vec = sym_matrix_to_vec(group_corr_mat)
        n_edges = group_corr_vec.shape[1]

        fc_fd_corr, fc_fd_pval = (np.zeros(n_edges) for _ in range(2))
        fc_fd_summary = []
        edges_weight = {}
        edges_weight_clean = {}

        for key, value in included.items():

            for i in range(n_edges):
                corr = pearsonr(group_corr_vec[value[0], i], group_conf_summary['mean_fd'].values[value[0]])
                fc_fd_corr[i] = corr[0]  # Pearson's r values
                fc_fd_pval[i] = corr[1]  # p-values

            fc_fd_corr = np.nan_to_num(fc_fd_corr)  # TODO: write exception

            # Calculate correlation between FC-FD r values and distance vector
            distance_dependence = pearsonr(fc_fd_corr, distance_vector)[0]

            # Store summary measure
            fc_fd_summary.append({"pipeline": pipeline_name,
                                  "perc_fc_fd_uncorr": np.sum(fc_fd_pval < 0.5) / len(fc_fd_pval) * 100,
                                  "pearson_fc_fd": np.median(fc_fd_corr),
                                  "distance_dependence": distance_dependence,
                                  "tdof_loss": group_conf_summary["n_conf"].mean(),
                                  "cleaned": value[1],
                                  "subjects": value[3],
                                  "sub_no": value[2]
                                  })
            # For cleaned dataset
            if value[1]:
                edges_weight_clean = {pipeline_name: group_corr_vec[value[0]].mean(axis=0)}

            # For full dataset
            if not value[1]:
                edges_weight = {pipeline_name: group_corr_vec[value[0]].mean(axis=0)}

            # Plotting FC and FC-FD correlation matrices
            fc_fd_corr_mat = vec_to_sym_matrix(fc_fd_corr)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

            fig1 = ax1.imshow(group_corr_mat[value[0]].mean(axis=0), vmin=-1, vmax=1, cmap="RdBu_r")
            ax1.set_title(f"{pipeline_name}: mean FC")
            fig.colorbar(fig1, ax=ax1)

            fig2 = ax2.imshow(fc_fd_corr_mat, vmin=-1, vmax=1, cmap="RdBu_r")
            ax2.set_title(f"{pipeline_name}: FC-FD correlation")
            fig.colorbar(fig2, ax=ax2)
            fig.suptitle(f"{pipeline_name}: {key}")

            fig.savefig(join(self.inputs.output_dir, f"FC_FD_corr_mat_{pipeline_name}_{value[3].lower()}.png"),
                        dpi=300)

            self._results["fc_fd_summary"] = fc_fd_summary
            self._results["edges_weight"] = edges_weight
            self._results["edges_weight_clean"] = edges_weight_clean

        return runtime


class MergeGroupQualityMeasuresOutputSpec(TraitedSpec):
        fc_fd_summary = traits.List()
        edges_weight = traits.List()
        edges_weight_clean = traits.List()


class MergeGroupQualityMeasuresInputSpec(BaseInterfaceInputSpec):
    fc_fd_summary = traits.List()
    edges_weight = traits.List()
    edges_weight_clean = traits.List()


class MergeGroupQualityMeasures(SimpleInterface):
    input_spec = MergeGroupQualityMeasuresInputSpec
    output_spec = MergeGroupQualityMeasuresOutputSpec

    def _run_interface(self, runtime):
        self._results['fc_fd_summary'] = self.inputs.fc_fd_summary
        self._results['edges_weight'] = self.inputs.edges_weight
        self._results['edges_weight_clean'] = self.inputs.edges_weight_clean
        return runtime


class PipelinesQualityMeasuresInputSpec(BaseInterfaceInputSpec):

    fc_fd_summary = traits.List(
        exists=True,
        desc="QC-FC quality measures")

    edges_weight = traits.List(
        exists=True,
        desc="Weights of individual edges")

    edges_weight_clean = traits.List(
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

    pipelines_edges_weight_clean = File(
        exists=True,
        desc="Group weights of individual edges")

class PipelinesQualityMeasures(SimpleInterface):
    input_spec = PipelinesQualityMeasuresInputSpec
    output_spec = PipelinesQualityMeasuresOutputSpec

    def _run_interface(self, runtime):

        # Convert merged quality measures to pd.DataFrame
        pipelines_fc_fd_summary = pd.DataFrame(
            list(chain.from_iterable(list(chain.from_iterable(self.inputs.fc_fd_summary)))))

        pipelines_edges_weight = pd.DataFrame()
        pipelines_edges_weight_clean = pd.DataFrame()

        for edges in zip(self.inputs.edges_weight):
            pipelines_edges_weight = pd.concat([pipelines_edges_weight, pd.DataFrame(edges[0][0])], axis=1)

        for edges_clean in zip(self.inputs.edges_weight_clean):
            pipelines_edges_weight_clean = pd.concat([pipelines_edges_weight_clean, pd.DataFrame(edges_clean[0][0])], axis=1)

        fname1 = join(self.inputs.output_dir, f"pipelines_fc_fd_summary.tsv")
        fname2 = join(self.inputs.output_dir, f"pipelines_edges_weight.tsv")
        fname3 = join(self.inputs.output_dir, f"pipelines_edges_weight_clean.tsv")

        pipelines_fc_fd_summary.to_csv(fname1, sep='\t', index=False)
        pipelines_edges_weight.to_csv(fname2, sep='\t', index=False)
        pipelines_edges_weight_clean.to_csv(fname3, sep='\t', index=False)

        # ----------------------
        # Plot quality measures
        # ----------------------

        # Density plot (all subjects)
        fig1, ax = plt.subplots(1, 1)

        for col in pipelines_edges_weight:
            sns.kdeplot(pipelines_edges_weight[col], shade=True)
            plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
            plt.title("Density of edge weights (all subjects)")

        fig1.savefig(f"{self.inputs.output_dir}/pipelines_edges_density.svg", dpi=300)

        # Density plot (no high motion)
        fig1_2, ax = plt.subplots(1, 1)

        for col in pipelines_edges_weight_clean:
            sns.kdeplot(pipelines_edges_weight_clean[col], shade=True)
            plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
            plt.title("Density of edge weights (no high motion)")

        fig1_2.savefig(f"{self.inputs.output_dir}/pipelines_edges_density_no_high_motion.svg", dpi=300)

        # Boxplot (Pearson's r FC-DC)
        fig2 = sns.catplot(x="pearson_fc_fd",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC (Pearson's r)",
                                    ylabel='Pipeline')
        fig2.savefig(f"{self.inputs.output_dir}/pipelines_fc_fd_pearson.svg", dpi=300, bbox_inches="tight")

        # Boxplot (% correlated edges)
        fig3 = sns.catplot(x="perc_fc_fd_uncorr",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="QC-FC uncorrected (%)",
                                    ylabel='Pipeline')

        fig3.savefig(f"{self.inputs.output_dir}/pipelines_fc_fd_uncorr.svg", dpi=300, bbox_inches="tight")

        # Boxplot (Pearson's r FC-DC with distance)

        fig4 = sns.catplot(x="distance_dependence",
                    y="pipeline",
                    col='subjects',
                    kind='bar',
                    data=pipelines_fc_fd_summary,
                    orient="h").set(xlabel="Distance-dependence",
                                    ylabel='Pipeline')
        fig4.savefig(f"{self.inputs.output_dir}/pipelines_distance_dependence.svg", dpi=300, bbox_inches="tight")

        self._results['pipelines_fc_fd_summary'] = fname1
        self._results['pipelines_edges_weight'] = fname2
        self._results['pipelines_edges_weight_clean'] = fname3

        return runtime