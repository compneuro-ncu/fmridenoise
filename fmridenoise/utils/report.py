import jinja2
from os.path import join, dirname, exists
import glob

YES = '\u2713'
NO = '\u2717'
NA = 'N/A'

def get_pipeline_summary(pipeline):

    """Generates list of dictionaries with setting summary for pipeline.

    Args:
        pipeline: Dictionary with pipeline setup (from .json file)

     Returns:
        pipeline_list: list of dictionaries with pipeline setup.
    """
    confounds = {"wm": "WM",
                 "csf": "CSF",
                 "gs": "GS",
                 "acompcor": "aCompCor",
                 "aroma": "ICA-AROMA",
                 "spikes": "Spikes"}

    pipeline_list = []

    for conf, conf_name in confounds.items():

        if conf == "aroma":
            raw = YES if pipeline[conf] else NO
            temp_deriv = NA
            quad_terms = NA
        elif conf == "spikes":
            raw = YES if pipeline[conf] else NO
            temp_deriv = NA
            quad_terms = NA

        else:
            raw = YES if pipeline["confounds"][conf] else NO

            if not pipeline["confounds"][conf]:
                temp_deriv = NO
                quad_terms = NO

            if isinstance(pipeline["confounds"][conf], dict):

                if pipeline["confounds"][conf]['temp_deriv']:
                    temp_deriv = YES

                if pipeline["confounds"][conf]['quad_terms']:
                    quad_terms = YES

        pipeline_dict = {"Confound": conf_name,
                        "Raw": raw,
                        "Temp. deriv.": temp_deriv,
                        "Quadr. terms": quad_terms}
        pipeline_list.append(pipeline_dict)

    return(pipeline_list)


def create_pipelines_data_dict(data_path: str, pipelines_list: list) -> dict:
    output = {}
    output['pipelines'] = []
    for pipeline in pipelines_list:
        no_high_motion = "FC_FD_corr_mat_" + pipeline['name'] + '_no_high_motion.png'
        all = "FC_FD_corr_mat_" + pipeline['name'] + '_all.png'
        if not exists(join(data_path, no_high_motion)) \
            and not exists(join(data_path, all)):
            raise FileNotFoundError(f"Corelation matrix for {pipeline} is missing!")
        
        pipeline_dict = {'name': pipeline['name'],
                         'description': pipeline['description'],
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
    data_dict = create_pipelines_data_dict(data_path, pipelines_list)
    data_dict['group'] = {}
    data_dict['group']['img'] = {'Edges_Density': join(data_path, 'pipelines_edges_density.svg'),
                                 'Edges_Density_No_High_Motion': join(data_path, 'pipelines_edges_density_no_high_motion.svg'),
                                 'Pipelines_Distance_Dependency': join(data_path, 'pipelines_distance_dependence.svg'),
                                 'Pipelines_FC_FC_Pearson': join(data_path, 'pipelines_fc_fd_pearson.svg'),
                                 'Motion_Out': glob.glob(join(data_path, "motion_criterion*"))[0]}
    html = tpl.render(data_dict, css=css)
    with open(join(data_path, 'report.html'), 'w') as report_file:
        report_file.write(html)

if __name__ == '__main__':
    from fmridenoise.utils.utils import load_pipeline_from_json
    from fmridenoise.pipelines import get_pipeline_path
    path = '/mnt/dane/small/derivatives/fmridenoise'
    pipelines_list = [load_pipeline_from_json(get_pipeline_path('pipeline-Null')),
                      load_pipeline_from_json(get_pipeline_path('pipeline-24HMP_8Phys_SpikeReg'))]
    create_report(path, pipelines_list)