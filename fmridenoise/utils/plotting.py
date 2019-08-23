import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def motion_plot(group_conf_summary):
    # Plot style setup
    plt.style.use('seaborn-white')
    plt.rcParams['font.family'] = 'Helvetica'
    colour = ["#fe6863", "#00a074"]
    palette = sns.set_palette(colour)

    small = 15
    plt.rc('font', size=small)  # controls default text sizes
    plt.rc('axes', titlesize=small)  # fontsize of the axes title
    plt.rc('axes', linewidth=2.2)
    plt.rc('axes', labelsize=small)  # fontsize of the x and y labels
    plt.rc('xtick', labelsize=small)  # fontsize of the tick labels
    plt.rc('ytick', labelsize=small)  # fontsize of the tick labels
    plt.rc('legend', fontsize=small)  # legend fontsize
    plt.rc('lines', linewidth=2.2, color='gray')
    # ------------------------------------------

    motion_dict = {'Mean FD': ['mean_fd', 0.2],
                   'Max FD': ['max_fd', 5],
                   'Percent of outlier dataframes (%)': ['perc_spikes', 20]}

    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    fig.subplots_adjust(wspace=0.4, hspace=0.4)

    i = 0
    for key, value in motion_dict.items():
        plt.figure(figsize=(4, 6))
        p = sns.swarmplot(y=value[0],
                          x="task",
                          hue="include",
                          data=group_conf_summary,
                          alpha=0.8,
                          s=10,
                          color=palette,
                          ax=axes[i]
                          )

        p = sns.boxplot(y=value[0],
                        x="task",
                        data=group_conf_summary,
                        showcaps=False,
                        boxprops={'facecolor': 'None'},
                        showfliers=False, ax=axes[i])

        p.title.set_text(f"Threshold = {value[1]}")
        p.axhline(value[1], ls='--', color="#fe6863")
        p.set(xlabel='')
        p.set(ylabel=key)
        p.get_legend().set_visible(False)
        p.tick_params(axis='both', which='both', length=6, width=2.2)
        i += 1
    fig.suptitle(f"Excluding high motion subjects", va="top")

    return fig