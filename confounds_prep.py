import pandas as pd
import numpy as np


def get_confounds_deriv(dataframe, temp_deriv = False, quad_terms = False):

    """Function that calculates temporal derivatives and quadratic terms
    for each column of pandas dataframe.

    Parameters
    ----------
    dataframe: pandas dataframe with variable to calculate temporal derivarives

    Returns
    -------
    regressors:  pandas dataframe including original columns and their temporal derivatives ('_td')
                 and (optional) their quadratic terms ('_quad')

    """

    regressors = dataframe.copy()

    if temp_deriv == True:
        for col in regressors.columns:
            temp = np.diff(regressors[col], 1, axis=0)
            temp = np.insert(temp, 0, 0)
            regressors[col + '_td'] = pd.DataFrame(temp)

    if quad_terms == True:
        for col in regressors.columns:
            regressors[col + '_quad'] = regressors[col] ** 2

    return regressors


def get_outliers(column, th):

    """Function that calculates outliers above specified threshold.

    Parameters
    ----------
    dataframe: single column dataframe
    th: threshold

    Returns
    -------
    outliers:  boolean array with True in outier data points

    """

    if th == None:
        return np.zeros(column.size, dtype=bool)
    else:
        variable = column.copy()
        variable.fillna(value=0, inplace=True)
        outliers = np.absolute(variable.astype(float)) > th

        return outliers.iloc[:,0].values


def get_spikes_regressors(outliers):
    """Function that generates separate column for each spike regressor

    Parameters
    ----------
    outliers: boolean array with True value for each outlier datapoint

    Returns
    -------
    spike regressors:  pd.DataFrame with columns representing each separate spikes

    """

    spikes = pd.DataFrame()

    count = 1
    for i, val in enumerate(outliers):
        if val == True:
            zeros_vec = np.zeros(outliers.size)
            zeros_vec[i] = 1
            spikes[f'spike_{count:03}'] = zeros_vec
            count+=1

    return spikes


def get_confounds_table(confounds_table_raw, pipeline):

    """Function that takes each individual confounds table and denoising pipeline
    and returns filtered and processed table which can be used for denoising.

    Parameters
    ----------
    confounds_table_raw: pd.DataFrame with counfounds fMRIPrep output
    pipeline: dictionary storing denoising pipeline set-up

    Returns
    -------
    filtered confound table:  pd.DataFrame with all regresors and their derivarives
    for specified pipeline.

    """

    pipeline_sel = pipeline.copy()
    confounds_raw = confounds_table_raw.copy()
    confounds_prep = pd.DataFrame()

    confounds = [key for key in pipeline['confounds']]
    spikes = [key for key in pipeline['spikes']]

    confounds_colnames = {
        'wm': ['WhiteMatter'],
        'csf': ['CSF'],
        'gs': ['GlobalSignal'],
        'motion': ['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ'],
        'acomp_cor': ['aCompCor01', 'aCompCor02', 'aCompCor03', 'aCompCor04', 'aCompCor05']
        }

    spikes_colnames = {
        'fd': 'FramewiseDisplacement',
        'dvars': 'stdDVARS'
    }

    for confound in confounds:
        confound_type = pipeline['confounds'][confound]
        if confound_type:
            opt = pipeline['confounds'][confound]
            temp = pd.DataFrame(confounds_raw, columns = list(confounds_colnames[confound]))
            confound_deriv = get_confounds_deriv(temp, temp_deriv=opt['temp_deriv'],
                                                 quad_terms=opt['quad_terms'])
            confounds_prep = pd.concat([confounds_prep, confound_deriv], axis=1)

    if pipeline['spikes']:
        fd_col = pd.DataFrame(confounds_raw, columns = list(['FramewiseDisplacement']))
        dvars_col = pd.DataFrame(confounds_raw, columns = list(['stdDVARS']))

        fd_out = get_outliers(fd_col, pipeline['spikes']['fd_th'])
        dvars_out = get_outliers(dvars_col, pipeline['spikes']['dvars_th'])
        outliers = (fd_out== True) | (dvars_out == True)
        spike_regressors = get_spikes_regressors(outliers)
        confounds_prep = pd.concat([confounds_prep, spike_regressors], axis=1)

    return confounds_prep
