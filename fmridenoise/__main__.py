import argparse
import logging
import os
from os.path import dirname, abspath, join, exists, isfile, abspath
import sys
# asure that fmridenoise is in path
# if dirname(dirname(abspath(__file__))) not in sys.path:
#         sys.path.append(dirname(dirname(abspath(__file__))))
from fmridenoise.workflows.base import init_fmridenoise_wf, config
from fmridenoise.utils import profiler_callback
from fmridenoise.utils.json_validator import is_valid
import fmridenoise.utils.utils as ut
from fmridenoise.pipelines import (get_pipelines_paths,
                                   get_pipelines_names,
                                   get_pipeline_path)

HIGH_PASS_DEFAULT = 0.008
LOW_PASS_DEFAULT = 0.08


def get_parser() -> argparse.ArgumentParser:
    """
    Creates parser for main script.
    :return: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("bids_dir",
                        help="Path do preprocessed BIDS dataset.")
    parser.add_argument('-sub', "--subjects",
                        nargs='+',
                        default=[],
                        help="List of subjects")
    parser.add_argument('-ses', "--sessions",
                        nargs='+',
                        default=[],
                        help="List of session numbers, separated with spaces.")
    parser.add_argument('-t', "--tasks",
                        nargs="+",
                        default=[],
                        help="List of tasks names, separated with spaces.")
    parser.add_argument("-p", "--pipelines",
                        nargs='+',
                        help='Name of pipelines used for denoising, can be both paths to json files with pipeline or name of pipelines from package.',
                        default="all")
    parser.add_argument("-d", "--derivatives",
                        nargs="+",
                        default=['fmriprep'],
                        help="Name (or list) of derivatives for which fmridenoise should be run.\
                        By default workflow looks for fmriprep dataset.")
    parser.add_argument("--high-pass",
                        type=float,
                        default=HIGH_PASS_DEFAULT,
                        help=f"High pass filter value, deafult {HIGH_PASS_DEFAULT}.")
    parser.add_argument("--low-pass",
                        type=float,
                        default=LOW_PASS_DEFAULT,
                        help=f"Low pass filter value, default {LOW_PASS_DEFAULT}")
    parser.add_argument("--no-ica-aroma",
                        help="Skip ICA-AROMA pipelines, default True",
                        action="store_false",
                        default=True)
    parser.add_argument("--MultiProc",
                        help="Run script on multiple processors, default False",
                        action="store_true",
                        default=False)
    parser.add_argument("--profiler",
                        type=str,
                        help="Run profiler along workflow execution to estimate resources usage \
                        PROFILER is path to output log file.")
    parser.add_argument("-g", "--debug",
                        help="Run fmridenoise in debug mode - richer output, stops on first unchandled exception.",
                        action="store_true")
    parser.add_argument("--graph",
                        type=str,
                        help="Create workflow graph at GRAPH path")
    parser.add_argument("--dry",
                        help="Perform everything except actually running workflow",
                        action="store_true",
                        default=False)
    return parser


def parse_pipelines(pipelines_args: str or set = "all") -> set:
    """
    Parses all possible pipeline options:
    :param pipelines_args: set or str, only valid string argument is 'all'.
    If argument is set it can containing both names of pipelines from
    fmridenoise.pipelines directory or path(s) to valid json file(s)
    containing of valid pipeline description.
    :return: set of valid pipelines paths.
    """
    if type(pipelines_args) is str:
        if pipelines_args != "all":
            raise ValueError("Only valid string argument is 'all'")
        else:
            return get_pipelines_paths()
    known_pipelines = get_pipelines_names()
    pipelines_args = set(pipelines_args)
    if pipelines_args <= known_pipelines:
        return get_pipelines_paths(pipelines_args)
    ret = set()
    for p in pipelines_args:
        if p in known_pipelines:
            ret.add(get_pipeline_path(p))    
        elif p not in known_pipelines and is_valid(ut.load_pipeline_from_json(p)):
            ret.add(p)
        else:
            raise ValueError(f"File: '{p} is not a valid pipeline")
    return ret


def main() -> None:
    args = get_parser().parse_args()
    workflow_args = dict()
    # bids dir
    if str(args.bids_dir).startswith("./"):
        input_dir = join(os.getcwd(), args.bids_dir[2:])
    else:
        input_dir = args.bids_dir
    # debug
    if args.debug:
        logs_dir = join(dirname(__file__), "logs")
        config.set_log_dir(logs_dir)
        config.enable_resource_monitor()
        config.enable_debug_mode()
    # profiler
    if args.profiler is not None:
        profiler_path = abspath(args.profiler)
        workflow_args['status_callback'] = profiler_callback
        if exists(profiler_path):
            if not isfile(profiler_path):
                raise OSError("Logs path is a directory.")
        else:
            os.makedirs(dirname(profiler_path), exist_ok=True)
        logger = logging.getLogger('callback')
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(profiler_path)
        logger.addHandler(handler)
        config.enable_resource_monitor()
    # derivatives
    derivatives = args.derivatives if type(args.derivatives) in (list, bool) else [args.derivatives]
    derivatives = list(map(lambda x: join(input_dir, 'derivatives', x), derivatives))
    # pipelines
    pipelines = parse_pipelines(args.pipelines)
    # creating workflow
    workflow = init_fmridenoise_wf(input_dir, 
                                   derivatives=derivatives,
                                   subject=args.subjects,
                                   session=args.sessions,
                                   task=args.tasks,
                                   pipelines_paths=pipelines,
                                   high_pass=args.high_pass,
                                   low_pass=args.low_pass,
                                   ica_aroma=args.no_ica_aroma)
    # creating graph from workflow
    if args.graph is not None:
        try:  # TODO: Look for pydot/dot and add to requirements
            workflow.write_graph(args.graph)
        except OSError as err:
            print('OSError: ' + err.args[0])
            print("         Graph file was not generated.")
    
    # dry
    if not args.dry:
        # linear/multiproc
        if args.MultiProc:
            workflow_args['maxtasksperchild'] = 1
            workflow.run(plugin="MultiProc", plugin_args=workflow_args)
        else:
            workflow.run()
    return 0

if __name__ == "__main__":
    main()
