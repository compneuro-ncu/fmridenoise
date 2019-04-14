import pandas as pd
import numpy as np

def get_temp_derivative(confound):
    ''''''
    confound_copy = confound.copy()
    return pd.Series(np.ediff1d(confound_copy, to_begin=0),
                     name=confound_copy.name + '_td')

def get_quad_term(confound):
    ''''''
    confound_copy = confound.copy()
    return pd.Series(confound_copy ** 2,
                     name=confound_copy.name + '_quad')

def get_outliers(column: pd.Series, th):

    """Function that calculates outliers above specified threshold.

    Parameters
    ----------
    column: single column dataframe
    th: threshold

    Returns
    -------
    outliers:  boolean array with True in outier data points

    """
    if not issubclass(type(th), (int, float)): # TODO: Better check for numeric types
        raise TypeError("treshold should be float, but is {}".format(type(th)))

    return np.array(np.absolute(column.fillna(0).astype(float)) > th)


def get_spikes_regressors(outliers):
    """Function that generates separate column for each spike regressor

    Parameters
    ----------
    outliers: boolean array with True value for each outlier datapoint

    Returns
    -------
    spike regressors:  pd.DataFrame with columns representing each separate
        spikes

    """

    spikes = pd.DataFrame()

    count = 1
    for i, val in enumerate(outliers):
        if val:
            zeros_vec = np.zeros(outliers.size)
            zeros_vec[i] = 1
            spikes[f'spike_{count:03}'] = zeros_vec
            count += 1

    return spikes


def get_confounds_table(confounds_table_raw, pipeline):

    """Function that takes each individual confounds table and denoising
    pipeline and returns filtered and processed table which can be used for
    denoising.

    Parameters
    ----------
    confounds_table_raw: pd.DataFrame with counfounds fMRIPrep output
    pipeline: dictionary storing denoising pipeline set-up

    Returns
    -------
    filtered confound table:  pd.DataFrame with all regresors and their
        derivarives for specified pipeline.

    """
    confounds_raw = confounds_table_raw.copy() # THINK ABOUT NAMING
    confounds_prep = pd.DataFrame()

    confounds_colnames = {'wm': ['WhiteMatter'],
                          'csf': ['CSF'],
                          'gs': ['GlobalSignal'],
                          'motion': ['X', 'Y', 'Z', 'RotX', 'RotY', 'RotZ'],
                          'acompcor': ['aCompCor01', 'aCompCor02', 'aCompCor03',
                                        'aCompCor04', 'aCompCor05']}

    spikes_colnames = {'fd': 'FramewiseDisplacement', 'dvars': 'stdDVARS'}

    # Deal with regular confounds
    for ckey, cval in pipeline['confounds'].items():

        if cval: # Confound included
            temp = confounds_raw[confounds_colnames[ckey]]
            confounds_prep = pd.concat([confounds_prep, temp], axis=1)

            if cval['temp_deriv']: # Include temporal derivatives
                for colname in temp:
                    confounds_prep = pd.concat(
                        [confounds_prep,
                         get_temp_derivative(temp[colname]).to_frame()],
                        axis=1)

            if cval['quad_terms']: # Include quadratic terms
                for colname in temp:
                    confounds_prep = pd.concat(
                        [confounds_prep,
                         get_quad_term(temp[colname])],
                        axis=1)

    if pipeline['spikes']:

        if pipeline['spikes']['fd_th']:
            fd_out = get_outliers(
                confounds_raw[spikes_colnames['fd']],
                pipeline['spikes']['fd_th'])

        if pipeline['spikes']['dvars_th']:
            dvars_out = get_outliers(
                confounds_raw[spikes_colnames['dvars']],
                pipeline['spikes']['dvars_th'])

        # Both spike options are selected
        if None not in pipeline['spikes'].values():
            outliers = (fd_out == True) | (dvars_out == True)
        elif pipeline['spikes']['fd_th']:
            outliers = fd_out
        else:
            outliers = dvars_out

        spike_regressors = get_spikes_regressors(outliers)
        confounds_prep = pd.concat([confounds_prep, spike_regressors], axis=1)

        return confounds_prep
