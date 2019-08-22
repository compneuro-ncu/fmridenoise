import jinja2
from os.path import join, dirname, exists
import glob

def get_pipeline_summary(pipeline):

    """Generates list of dictionaries with setting summary for pipeline.

    Args:
        pipeline: Dictionary with pipeline setup (from .json file)

     Returns:
        pipeline_list: list of dictionaries with pipeline setup.
    """
    YES = '\u2713'
    NO = '\u2717'
    confounds = {"wm": "WM",
                 "csf": "CSF",
                 "gs": "GS",
                 "acompcor": "aCompCor",
                 "aroma": "ICA-Aroma",
                 "spikes": "Spikes"}

    pipeline_list = []

    for conf, conf_name in confounds.items():

        if conf != "aroma":
            if conf != "spikes":
                raw = YES if pipeline["confounds"][conf] else NO

                if not pipeline["confounds"][conf]:
                    temp_deriv = NO
                    quad_terms = NO

                if isinstance(pipeline["confounds"][conf], dict):

                    if pipeline["confounds"][conf]['temp_deriv']:
                        temp_deriv = YES

                    if pipeline["confounds"][conf]['quad_terms']:
                        quad_terms = YES

        if conf == "aroma":
            raw = YES if pipeline[conf] else NO
            temp_deriv = NO
            quad_terms = NO

        if conf == "spikes":
            raw = YES if pipeline[conf] else NO
            temp_deriv = NO
            quad_terms = NO

        pipeline_dict = {"Confound": conf_name,
                         "Raw": raw,
                         "Temp. deriv.": temp_deriv,
                         "Quadr. terms": quad_terms}

        pipeline_list.append(pipeline_dict)

    return(pipeline_list)

def create_data_dict(data_path: str, pipelines_list: list) -> dict:
    output = {}
    output['pipelines'] = []
    for pipeline in pipelines_list:
        no_high_motion = "FC_FD_corr_mat_" + pipeline['name'] + '_no_high_motion.png'
        all = "FC_FD_corr_mat_" + pipeline['name'] + '_all.png'
        if not exists(join(data_path, no_high_motion)) \
            and not exists(join(data_path, all)):
            raise FileNotFoundError(f"Corelation matrix for {pipeline} is missing!")
        
        pipeline_dict = {'name': pipeline['name'],
                         'corelation_matrix_all': all,
                         'corelation_matrix_no_high_motion': no_high_motion,
                         'summary': get_pipeline_summary(pipeline)}
        output['pipelines'].append(pipeline_dict)
    return output


def create_report(data_path: str, pipelines_list: list) -> None:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            searchpath=join(dirname(__file__), 'templates')))
    css_template = env.get_template('report.css')
    css = css_template.render()
    tpl = env.get_template('report_template.html')
    data_dict = create_data_dict(data_path, pipelines_list)
    html = tpl.render(data_dict, css=css)
    with open(join(data_path, 'report.html'), 'w') as report_file:
        report_file.write(html)

if __name__ == '__main__':
    path = '/mnt/dane/small/derivatives/fmridenoise'
    pipelines_list = [{
        "name": "36_parameters_gs",
        "description": "",
        "confounds":
        {
            "wm":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "csf":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "gs":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "motion":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "acompcor": "False"
        },
        "aroma": "False",
        "spikes":
        {
            "fd_th": 0.5,
            "dvars_th": 3
        }
    }, {
        "name": "36_parameters",
        "description": "",
        "confounds":
        {
            "wm":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "csf":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "gs": "False",
            "motion":
            {
                "temp_deriv": "True",
                "quad_terms": "True"
            },
            "acompcor": "False"
        },
        "aroma": "False",
        "spikes":
        {
            "fd_th": 0.5,
            "dvars_th": 3
        }
    }]
    create_report(path, pipelines_list)