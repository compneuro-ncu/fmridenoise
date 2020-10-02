import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def make_motion_plot(group_conf_summary, output_path, mean_fd_th=0.2, max_fd_th=5, perc_spikes_th=20):
    """Generates plot presenting number of subjects excluded with high motion
    according specified thresholds."""

    sns.set_style("ticks")
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

    columns = ['mean_fd', 'max_fd']
    thresholds = [mean_fd_th, max_fd_th]
    if 'perc_spikes' in group_conf_summary.columns:
        columns += ['perc_spikes']
        thresholds += [perc_spikes_th]
    fig, axes = plt.subplots(1, len(columns), figsize=(16, 7))
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
    fig.savefig(output_path, dpi=300)
    plt.clf()
    return fig


def make_kdeplot(data, title, output_path):
    """Creates and saves kdeplot from dataframes with edges."""
    sns.set_style("ticks")
    sns.set_palette('colorblind', 8)

    fig, ax = plt.subplots(1, 1)
    for col in data:
        sns.kdeplot(data[col], shade=True)

    plt.axvline(0, 0, 2, color='gray', linestyle='dashed', linewidth=1.5)
    plt.title(title)
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.clf()
    return output_path


def make_catplot(x, data, xlabel, output_path):
    """Creates and saves catplot from summary dataframes """

    sns.set_palette('colorblind', 8)
    fig = sns.catplot(x=x,
                      y='pipeline',
                      kind='bar',
                      data=data,
                      orient="h").set(xlabel=xlabel,
                                      ylabel='Pipeline')

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.clf()
    return output_path


def make_barplot(x, data, xlabel, output_path):
    """Creates and saves barplot from summary dataframes """
    sns.set_palette('colorblind', 8)
    sns.set_style("ticks")

    fig = sns.barplot(x=x,
                      y='pipeline',
                      data=data,
                      edgecolor=".2",
                      linewidth=1,
                      orient="h").set(xlabel=xlabel,
                                      ylabel='Pipeline')

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.clf()
    return output_path


def make_violinplot(data, xlabel, output_path):
    """Creates and saves violinplot from FC-FD correlation values"""
    sns.set_palette('colorblind', 8)
    sns.set_style("ticks")

    sns.violinplot(data=data,
                   edgecolor=".2",
                   linewidth=1,
                   orient="h").set(xlabel=xlabel,
                                   ylabel='Pipeline')

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.clf()
    return output_path
