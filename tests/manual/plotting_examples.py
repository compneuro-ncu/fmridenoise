import os
import pathlib
from io import StringIO

import numpy as np
import pandas as pd
from fmridenoise.interfaces.quality_measures import PipelinesQualityMeasures
from fmridenoise.utils.plotting import (
    make_carpetplot,
    make_catplot,
    make_corr_matrix_plot,
    make_kdeplot,
    make_motion_plot,
    make_violinplot,
)

if __name__ == '__main__':

    PLOTS_PATH = pathlib.Path(__file__).parent.joinpath('plots')
    PLOTS_PATH.mkdir(exist_ok=True)

    # plotting functions used in PipelineQualityMeasures
    # raw data from existing dataset
    raw_data = [
        [
            {
                'perc_fc_fd_uncorr': 5.189054726368159,
                'median_pearson_fc_fd': -0.026475392769353585,
                'distance_dependence': 0.015690398251139073,
                'tdof_loss': 33.5,
                'n_subjects': 4,
                'n_excluded': 0,
                'all': True,
                'pipeline': '24HMPaCompCorSpikeReg',
            },
            {
                'perc_fc_fd_uncorr': 5.189054726368159,
                'median_pearson_fc_fd': -0.026475392769353585,
                'distance_dependence': 0.015690398251139073,
                'tdof_loss': 33.5,
                'n_subjects': 4,
                'n_excluded': 0,
                'all': False,
                'pipeline': '24HMPaCompCorSpikeReg',
            },
        ],
        [
            {
                'perc_fc_fd_uncorr': 4.303482587064677,
                'median_pearson_fc_fd': 0.07453020382237453,
                'distance_dependence': 0.04416598324412888,
                'tdof_loss': 32.0,
                'n_subjects': 4,
                'n_excluded': 0,
                'all': True,
                'pipeline': '24HMP8PhysSpikeReg',
            },
            {
                'perc_fc_fd_uncorr': 4.303482587064677,
                'median_pearson_fc_fd': 0.07453020382237453,
                'distance_dependence': 0.04416598324412888,
                'tdof_loss': 32.0,
                'n_subjects': 4,
                'n_excluded': 0,
                'all': False,
                'pipeline': '24HMP8PhysSpikeReg',
            },
        ],
    ]

    # shortened data from output based on existing dataset
    edges_weight = [
        {
            '24HMPaCompCorSpikeReg': np.array(
                [
                    0.70710678,
                    0.57153637,
                    0.70710678,
                    0.15028592,
                    0.63762674,
                    0.70710678,
                ]
            )
        },
        {
            '24HMP8PhysSpikeReg': np.array(
                [
                    0.70710678,
                    0.6222748,
                    0.70710678,
                    0.28966326,
                    0.72394566,
                    0.70710678,
                ]
            )
        },
    ]
    # shortened data from output based on existing dataset
    fc_fd_corr_values = [
        {
            '24HMPaCompCorSpikeReg': np.array(
                [0.0, -0.19478302, 0.0, 0.1532902, -0.49169747, 0.0]
            )
        },
        {
            '24HMP8PhysSpikeReg': np.array(
                [0.0, -0.75360801, 0.0, -0.64771381, -0.45432142, 0.0]
            )
        },
    ]
    fc_fd_corr_values_clean = fc_fd_corr_values
    edges_weight_clean = edges_weight
    fc_fd_summary = PipelinesQualityMeasures.pipeline_summaries_to_dataframe(
        raw_data
    )

    (
        edges_weight_df,
        edges_weight_clean_df,
    ) = PipelinesQualityMeasures.edges_weight_to_dataframe(
        edges_weight, edges_weight_clean
    )

    # save data
    edges_weight_df.to_csv(os.path.join(PLOTS_PATH, 'edges_weight.csv'))
    edges_weight_clean_df.to_csv(
        os.path.join(PLOTS_PATH, 'edges_weight_clean.csv')
    )
    fc_fd_summary.to_csv(os.path.join(PLOTS_PATH, 'fc_fd_summary.csv'))

    (
        fc_fd_corr_df,
        fc_fd_corr_clean_df,
    ) = PipelinesQualityMeasures.fc_fd_corr_values_to_dataframe(
        fc_fd_corr_values, fc_fd_corr_values_clean
    )

    print(fc_fd_corr_df)
    make_kdeplot(
        data=edges_weight_df,
        title="Example kdeplot",
        output_path=PLOTS_PATH.joinpath("kdeplot.png"),
    )
    make_catplot(
        x="perc_fc_fd_uncorr",
        y='pipeline',
        data=fc_fd_summary,
        xlabel="x data",
        output_path=PLOTS_PATH.joinpath("catplot.png"),
    )
    make_violinplot(
        data=fc_fd_corr_df,
        xlabel="x data",
        output_path=PLOTS_PATH.joinpath("violinplot.png"),
    )

    # plotting function used in QualityMeasures
    corr_matrix_data = np.random.random((100, 100))

    make_corr_matrix_plot(
        data=corr_matrix_data,
        title="Example corr matrix plot",
        ylabel="Pipeline name",
        output_path=PLOTS_PATH.joinpath("corr_matrix_plot.png"),
    )

    # motion plot
    group_conf_summary_content = (
        "subject	task	mean_fd	max_fd	n_conf	include	n_spikes	perc_spikes	session	run\n"
        "001	rest	0.006421440065068056	0.018733832384	32	True	0	0.0	LSD	1\n"
        "002	rest	0.005465743671052777	0.018818666798000004	32	True	0	0.0	LSD	1\n"
    )
    group_conf_summary = StringIO(initial_value=group_conf_summary_content)
    group_conf_summary_df = pd.read_csv(group_conf_summary, sep='\t')

    make_motion_plot(
        group_conf_summary=group_conf_summary_df,
        output_path=PLOTS_PATH.joinpath('motionplot.png'),
    )

    # plotting functions used in Connectivity
    time_series = np.random.random((100, 50))
    make_carpetplot(
        time_series=time_series, out_fname=PLOTS_PATH.joinpath('carpetplot.png')
    )
