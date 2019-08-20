def get_pipeline_summary(pipeline):

    """Generates list of dictionaries with setting summary for pipeline.

    Args:
        pipeline: Dictionary with pipeline set up (from .json file)
    """

    confounds = {"wm": "WM",
                 "csf": "CSF",
                 "gs":"GS",
                 "acompcor":"aCompCor",
                 "aroma":"ICA-Aroma",
                 "spikes": "Spikes"}

    pipeline_list = []

    for conf, conf_name in confounds.items():

        if conf != "aroma":
            if conf != "spikes":
                raw = ["Yes" if pipeline["confounds"][conf] else "No"][0]

                if not pipeline["confounds"][conf]:
                    temp_deriv = 'No'
                    quad_terms = 'No'

                if isinstance(pipeline["confounds"][conf], dict):

                    if pipeline["confounds"][conf]['temp_deriv']:
                        temp_deriv = 'Yes'

                    if pipeline["confounds"][conf]['quad_terms']:
                        quad_terms = 'No'

        if conf == "aroma":
            raw = ["Yes" if pipeline[conf] else "No"][0]
            temp_deriv = 'No'
            quad_terms = 'No'

        if conf == "spikes":
            raw = ["Yes" if pipeline[conf] else "No"][0]
            temp_deriv = 'No'
            quad_terms = 'No'

        pipeline_dict = {"Confound": conf_name,
                          "Raw": raw,
                          "Temp. deriv.": temp_deriv,
                          "Quadr. terms": quad_terms}

        pipeline_list.append(pipeline_dict)

    return(pipeline_list)