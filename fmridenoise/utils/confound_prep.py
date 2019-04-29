import numpy as np
import pandas as pd


def calc_temp_deriv(signal):
    """Calculates discrete version of temporal derivative of a timecourse.

    Args:
        signal (pd.Series): Timecourse of interest.

    Returns:
        np.array: Vector of differences between subsequent values in signal.
    """

    return np.ediff1d(signal, to_begin=0)


def calc_quad_term(signal):
    """Calculates squared values for a timecourse.

    Args:
        signal (pd.Series): Timecourse of interest.

    Returns:
        np.array: Vector of squared signal values.
    """
    return np.power(signal, 2)


def calc_outliers(conf_df_raw, pipeline):
    """Calculate outlier scans given the method specified in pipeline.

    Args:
        conf_df_raw (pd.DataFrame): Contains unprocessed confounds.
        pipeline (dict): Denoising pipeline specification.

    Returns:
        np.array: True for scans identified as outliers, False otherwise.
    """
    if not pipeline['spikes']: raise Exception('spike options not defined.')

    spikes_colnames = {
        'fd': 'framewise_displacement',
        'dvars': 'std_dvars'}

    fd_th = pipeline['spikes']['fd_th']        # Could be numeric or False
    dvars_th = pipeline['spikes']['dvars_th']  # Could be numeric or False

    if fd_th:
        fd_out = np.array(conf_df_raw[spikes_colnames['fd']] > fd_th)
    else:
        fd_out = np.zeros(len(conf_df_raw), dtype=bool)

    if dvars_th:
        dvars_out = np.array(conf_df_raw[spikes_colnames['dvars']] > dvars_th)
    else:
        dvars_out = np.zeros(len(conf_df_raw), dtype=bool)

    return np.logical_or(fd_out, dvars_out)


def get_spikes_regressors(conf_df_raw, pipeline):
    """Prepare spike regressors given the method specified in pipeline.

    Args:
        conf_df_raw (pd.DataFrame): Contains unprocessed confounds.
        pipeline (dict): Denoising pipeline specification.

    Returns:
        pd.DataFrame: Contains one spike regressor for each outlier scan. Shape
            is n_scans x n_outliers.
    """
    if not pipeline['spikes']: raise Exception('spike options not defined.')

    outliers = calc_outliers(conf_df_raw, pipeline)
    spikes_df = pd.DataFrame(
        np.eye(len(outliers))[np.nonzero(outliers)].T,
        index=conf_df_raw.index,
        dtype='int')
    spikes_df.rename(columns=lambda x: f'spike_{x}', inplace=True)

    return spikes_df


def get_confounds_regressors(conf_df_raw, pipeline):
    """Prepare confound regressors given the method specified in pipeline.

    Args:
        conf_df_raw (pd.DataFrame): Contains unprocessed confounds.
        pipeline (dict): Denoising pipeline specification.

    Returns:
        pd.DataFrame: Contains all relevant nuissance regressors and (if
            specified) their temporal derivatives and quadratic terms.
    """
    confounds_df = pd.DataFrame(index=conf_df_raw.index)
    conf_colnames = {
        'wm': ['white_matter'],
        'csf': ['csf'],
        'gs': ['global_signal'],
        'motion': ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'],
        'acompcor': ['a_comp_cor_00', 'a_comp_cor_01', 'a_comp_cor_02'
                     'a_comp_cor_03', 'a_comp_cor_04', 'a_comp_cor_05']}

    for conf_name in pipeline['confounds']:

        # Add proper columns from conf_df_raw
        if pipeline['confounds'][conf_name]:
            confounds_df = confounds_df.join(
                conf_df_raw[conf_colnames[conf_name]])

            # Calculate temporal derivatives and quadratic terms
            if conf_name in ['wm', 'csf', 'gs', 'motion']:

                    if pipeline['confounds'][conf_name]['temp_deriv']:
                        for conf_colname in conf_colnames[conf_name]:
                            confounds_df[conf_colname + '_td'] = \
                                calc_temp_deriv(confounds_df[conf_colname])

                    if pipeline['confounds'][conf_name]['quad_terms']:
                        for conf_colname in conf_colnames[conf_name]:
                            confounds_df[conf_colname + '_quad'] = \
                                calc_quad_term(confounds_df[conf_colname])
    return confounds_df


def prep_conf_df(conf_df_raw, pipeline):
    """Prepare final confound table given the methods specified in pipeline.

    Args:
        conf_df_raw (pd.DataFrame): Contains unprocessed confounds.
        pipeline (dict): Denoising pipeline specification.

    Returns:
        pd.DataFrame: Final confound regressors containing both spikes and
            nuissance regressors.
    """
    conf_df_prep = pd.DataFrame(index=conf_df_raw.index)

    # Confound signals with temporal derivaties and quadratic terms
    confounds_df = get_confounds_regressors(conf_df_raw, pipeline)
    conf_df_prep = conf_df_prep.join(confounds_df)

    # Spike regressors
    if pipeline['spikes']:
        spikes_df = get_spikes_regressors(conf_df_raw, pipeline)
        conf_df_prep = conf_df_prep.join(spikes_df)

    return conf_df_prep


