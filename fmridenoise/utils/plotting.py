import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from os.path import join


def make_motion_plot(group_conf_summary, pipeline_name, output_dir,
                     mean_fd_th=0.2, max_fd_th=5, perc_spikes_th=20):
    """Generates plot presenting number of subjects excluded with high morion
    according specified thresholds."""

    plt.style.use('seaborn-white')
    colors = ['#00a074', '#fe6863']
    palette = sns.set_palette(colors, 2)

    small = 15
    plt.rc('font', size=small)  # controls default text sizes
    plt.rc('axes', titlesize=small)  # fontsize of the axes title
    plt.rc('axes', linewidth=2.2)
    plt.rc('axes', labelsize=small)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=small)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=small)  # fontsize of the tick labels
    plt.rc('legend', fontsize=small)  # legend fontsize
    plt.rc('lines', linewidth=2.2, color='gray')

    columns = ['mean_fd', 'max_fd', 'perc_spikes']
    thresholds = [mean_fd_th, max_fd_th, perc_spikes_th]

    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.subplots_adjust(wspace=0.4, hspace=0.4)

    for i, (column, threshold) in enumerate(zip(columns, thresholds)):
        value = group_conf_summary[column] > threshold
        group_conf_summary['excluded'] = np.where(value == True, 1, 0)

        p = sns.swarmplot(y=column,
                          x="task",
                          data=group_conf_summary,
                          alpha=0.8,
                          s=10,
                          hue='excluded',
                          palette=palette,
                          ax=axes[i])

        p = sns.boxplot(y=column,
                        x="task",
                        data=group_conf_summary,
                        showcaps=False,
                        boxprops={'facecolor': 'None'},
                        showfliers=False, ax=axes[i])

        p.title.set_text(f'Threshold = {threshold}')
        p.axhline(threshold, ls='--', color="#fe6863")
        p.set(xlabel='')
        p.set(ylabel=column)
        p.get_legend().set_visible(False)
        p.tick_params(axis='both', which='both', length=6, width=2.2)

    fig.suptitle(f"Excluding high motion subjects", va="top")
    fig.savefig(join(output_dir, f"motion_criterion_pipeline-{pipeline_name}.svg"), dpi=300)

    return fig