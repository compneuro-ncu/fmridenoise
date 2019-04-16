import numpy as np
import pandas as pd

def calc_temp_deriv(signal):
    ''''''
    return np.ediff1d(signal, to_begin=0)

def calc_quad_term(signal):
    ''''''
    return np.power(signal, 2)

def calc_outliers(conf_df_raw, pipeline):
    ''''''
    if not pipeline['spikes']: raise Exception('spike options not defined.')

    spikes_colnames = {
        'fd': 'FramewiseDisplacement',
        'dvars': 'stdDVARS'}

    fd_th = pipeline['spikes']['fd_th']       # Could be numeric or False
    dvars_th = pipeline['spikes']['dvars_th'] # Could be numeric or False

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
    ''''''
    if not pipeline['spikes']: raise Exception('spike options not defined.')

    outliers = calc_outliers(conf_df_raw, pipeline)
    spikes_df = pd.DataFrame(
        np.eye(len(outliers))[np.nonzero(outliers)].T,
        index=conf_df_raw.index,
        dtype='int')
    spikes_df.rename(columns=lambda x: f'spike_{x}', inplace=True)

    return spikes_df

def get_confounds_regressors(conf_df_raw, pipeline):
    ''''''
    confounds_df = pd.DataFrame(index=conf_df_raw.index)
    conf_colnames = {
        'wm': ['WhiteMatter'],
        'csf': ['CSF'],
        'gs': ['GlobalSignal'],
        'motion': ['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ'],
        'acompcor': ['aCompCor01', 'aCompCor02',
                     'aCompCor03', 'aCompCor04', 'aCompCor05']}

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
    ''''''
    conf_df_prep = pd.DataFrame(index=conf_df_raw.index)

    # Confound signals with temporal derivaties and quadratic terms
    confounds_df = get_confounds_regressors(conf_df_raw, pipeline)
    conf_df_prep = conf_df_prep.join(confounds_df)

    # Spike regressors
    if pipeline['spikes']:
        spikes_df = get_spikes_regressors(conf_df_raw, pipeline)
        conf_df_prep = conf_df_prep.join(spikes_df)

    return conf_df_prep
