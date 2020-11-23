import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.pyplot import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable

rcDict = {
    'axes.linewidth': 1.3,
    'lines.linewidth': 1.3,
    'xtick.major.width': 1.3,
    'ytick.major.width': 1.3,
    'xtick.major.size': 3,
    'ytick.major.size': 3,
    'axes.spines.top': True,
    'font.size': 11.5,
    'figure.titlesize': 11.5,
    'axes.titlesize': 11.5,
    'legend.fancybox': True,
    'legend.edgecolor': 'k',
    'legend.fontsize': 11.5,
    'legend.framealpha': 0.25,
    'patch.linewidth': 1.3,
}


def make_motion_plot(
    group_conf_summary: pd.DataFrame,
    output_path: str,
    mean_fd_th: float = 0.2,
    max_fd_th: float = 5,
    perc_spikes_th: float = 20,
) -> Figure:
    """
    Generates plot presenting number of subjects excluded with high motion
    according specified thresholds.
    Args:
        group_conf_summary (DataFrame): dataframe, output from GroupConfounds
        output_path (str): output path where plot is saved
        mean_fd_th (float): mean frame displacement threshold
        max_fd_th (float): max frame displacement threshold
        perc_spikes_th (float): maximum percentage of unusually high frame displacement threshold

    Returns:
        created figure, ready to save
    """

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

        p = sns.swarmplot(
            y=column,
            x="task",
            data=group_conf_summary,
            alpha=0.8,
            s=10,
            hue='excluded',
            palette=palette,
            ax=axes[i],
        )

        p = sns.boxplot(
            y=column,
            x="task",
            data=group_conf_summary,
            showcaps=False,
            boxprops={'facecolor': 'None'},
            showfliers=False,
            ax=axes[i],
        )

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


def make_kdeplot(data, output_path, title=None):
    """
    Plot representing edge strenght distribution.

    Args:
        data (pd.DataFrame):
            Each column corresponds to single denoising strategy, each row
            correspond to connection strength. Column names will be used to
            create legend. DataFrame shape is n_edges x n_pipelines.
        output_path (str):
            Output path where plot is saved.
        title (str, optional):
            Plot title.

    Returns:
        Path for generated plot.
    """
    mpl.rcParams.update(
        rcDict
    )  # TODO: move outside after refactoring make_motion_plot
    fig, ax = plt.subplots(1, 1)

    for col in data:
        sns.kdeplot(data[col], shade=True, ax=ax)

    ax.axvline(x=0, linestyle='dashed', color='k')
    ax.set_title(title)
    ax.set_xlim([-1, 1])
    ax.set_ylabel("Probability density")
    ax.set_xlabel("Connection strength")
    ax.legend(bbox_to_anchor=(1.025, 1), borderaxespad=0)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path


def make_catplot(x, y, data, output_path, xlabel=None, ylabel=None):
    """
    Plot representing quality measure value for each pipeline.

    Args:
        x (str):
            Column name of data corresponding to quality measure.
        y (str):
            Column name of data used to group values.
        data (pd.DataFrame):
            Table of quality measures. It should contain at least one one column
            representing quality measure and one column for grouping variable.
            Usually each row corresponds to one pipeline.
        output_path (str):
            Output path where plot is saved.
        xlabel (str, optional):
            Custom x-axis label.
        ylabel (str, optional):
            Custom y-axis label.

    Returns:
        Path for generated plot.
    """
    mpl.rcParams.update(rcDict)
    fig = sns.catplot(x=x, y=y, kind='bar', data=data)
    if xlabel:
        fig.ax.set_xlabel(xlabel)
    if ylabel:
        fig.ax.set_ylabel(ylabel)

    sns.despine(top=False, right=False)
    fig.ax.axvline(x=0, color='k')
    if any([len(label.get_text()) > 10 for label in fig.ax.get_yticklabels()]):
        fig.ax.set_yticklabels(fig.ax.get_yticklabels(), fontSize=9)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    return output_path


def make_violinplot(data, output_path, xlabel=None):
    """Plot representing quality measure distribution for each pipeline.

    Args:
        data (pd.DataFrame):
            Table of quality measures. Each column represents single pipeline.
            Column names will be used as pipeline names. Values in each row
            correspond to quality measure used, usually there is one row for
            each network edge.
        output_path (str):
            Output path where plot is saved.
        xlabel (str, optional):
            Custom x-axis label.

    Returns:
        Path for generated plot.
    """
    mpl.rcParams.update(rcDict)
    fig, ax = plt.subplots(1, 1)

    edgewidth = 2.6  # Controls width of "violins"
    sns.violinplot(
        data=data,
        orient="h",
        inner="quartile",
        linewidth=edgewidth,
    )

    for poly in ax.collections:
        facecolor = poly.get_facecolor()[0]
        poly.set_edgecolor(facecolor)
        facecolor[-1] = 0.25
        poly.set_facecolor(facecolor)

    for l in ax.lines:
        l.set_linewidth(0)
    for idx, l in enumerate(ax.lines[1::3]):
        l.set_linestyle('-')
        l.set_linewidth(edgewidth)
        l.set_color(ax.collections[idx].get_edgecolor()[0])

    ax.axvline(x=0, color="k", linestyle=":", zorder=0)
    ax.set_ylabel("Pipeline")
    ax.set_xlabel(xlabel)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path


def make_corr_matrix_plot(
    data, output_path, title=None, ylabel=None, correlation=True
):
    """
    Plot representing correlation matrix.

    Args:
        data (numpy.ndarray):
            N x N correlation matrix.
        output_path (str):
            Output path where plot is saved.
        title (str, optional):
            Plot title.
        ylabel (str, optional):
            Custom y-axis label.
        correlation (bool, default True):
            If this flag is true, values are treated as correlations ranging
            from -1 to 1 automatically rescaling colorbar to that range.

    Returns:
        Path for generated plot.
    """
    mpl.rcParams.update(rcDict)
    fig, ax = plt.subplots(1, 1)

    im = ax.imshow(data, cmap='bwr', **{'clim': [-1, 1]} if correlation else {})
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)

    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path


def make_carpetplot(
    time_series: np.ndarray,
    out_fname: str,
    dpi=300,
    figsize=(8, 3),
    format='png',
):
    """Generates and saves carpet plot for rois timecourses.

    Args:
        time_series: Timecourse array of size N_timepoints x N_rois. Output of
            fit_transform() NiftiLabelsMasker method.
        out_fname: Carpetplot output filename.
        dpi (:obj:`int`, optional): Dots per inch (default 300).
        figsize (:obj:`tuple`, optional): Size of the figure in inches
            (default (3,8))
        format (:obj:`str`, optional): Image format. Available options include
            'png', 'pdf', 'ps', 'eps' and 'svg'.
    """
    if not isinstance(time_series, np.ndarray):
        raise TypeError('time series should be np.ndarray')

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111)

    ax.imshow(time_series.T, cmap='gray')
    ax.set_xlabel('volume')
    ax.set_ylabel('roi')
    ax.set_yticks([])

    try:
        fig.savefig(
            out_fname, format=format, transparent=True, bbox_inches='tight'
        )
    except FileNotFoundError:
        print(f'{out_fname} directory not found')
