import jinja2
import os

def create_report(report_data, output_dir, report_name='report.html'):

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), 'report_templates'))
        )

    pipeline_table = env.get_template('pipeline_table.j2')
    svg_definitions = env.get_template('svg_definitions.j2')
    report_style = env.get_template('report_style.css')
    report_base = env.get_template('report_base.j2')

    def render_pipeline_table(pipeline):
        return pipeline_table.render(pipeline=pipeline)

    report_html = report_base.render(
        report_style=report_style.render(),
        svg_definitions=svg_definitions.render(),
        report_data=report_data,
        render_pipeline_table=render_pipeline_table,
    )

    with open(os.path.join(output_dir, report_name), 'w') as report_file:
        report_file.write(report_html)

