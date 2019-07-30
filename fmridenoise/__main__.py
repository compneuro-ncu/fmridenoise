import argparse
from fmridenoise.utils.json_validator import is_valid
import fmridenoise.utils.utils as ut
from fmridenoise.pipelines import (get_pipelines_paths, 
                                   get_pipelines_names,
                                   get_pipeline_path)


def get_parser() -> argparse.ArgumentParser:
    """
    Creates parser for main script.
    :return: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("bids_dir", 
                        help="Path do preprocessed BIDS dataset.")
    parser.add_argument("-g", "--debug", 
                        help="Run fmridenois in debug mode", 
                        action="store_true")
    parser.add_argument("--graph", 
                        type=str, 
                        help="Create workflow graph at given path")
    parser.add_argument("-d", "--derivatives",
                        nargs="+",
                        default=['fmriprep'],
                        help="Name (or list) of derivatives for which fmridenoise should be run.\
                        By default workflow looks for fmriprep dataset.")
    parser.add_argument('-s', "--sessions",
                        nargs='+',
                        help="List of session numbers")
    parser.add_argument('-t', "--tasks",
                        nargs="+",
                        help="List of tasks names")
    parser.add_argument("-p", "--pipelines", 
                        nargs='+', 
                        help='Name of pipelines used for denoising',
                        default="all")
    parser.add_argument("--MultiProc",
                        help="EXPERIMENTAL: Run script on multiple processors, default False",
                        action="store_true",
                        default=False)
    parser.add_argument("--profiler", type=str, help="Run profiler along workflow execution to estimate resources usage \
                        PROFILER is path to output log file.")
    parser.add_argument("--dry",
                        help="Perform everything but do not run workflow",
                        action="store_true",
                        default=False)
    return parser


def parse_pipelines(pipelines_args: str or set = "all") -> set:
    """
    Parses all posible pipeline options:
    :param pipelines_args: set or str, only valid string argument is 'all'.
    If argument is set it can containg both names of pipelines from
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
        # elif p not in known_pipelines and is_valid(ut.load_pipeline_from_json(p)): 
        #     ret.add(p)
        else:
            raise ValueError(f"File: '{p} is not a valid pipeline")
    return ret


def main():
    import os
    from os.path import dirname, abspath, join
    import sys
    if dirname(dirname(abspath(__file__))) not in sys.path:
        sys.path.append(dirname(dirname(abspath(__file__))))
    from fmridenoise.workflows.base import init_fmridenoise_wf

               
    args = get_parser().parse_args()

    if str(args.bids_dir).startswith("./"):
        input_dir = join(os.getcwd(), args.bids_dir[2:])
    else:
        input_dir = args.bids_dir
    if args.debug:
        from fmridenoise.workflows.base import config
        logs_dir = join(dirname(__file__), "logs")
        config.set_log_dir(logs_dir)
        config.enable_resource_monitor()
        config.enable_debug_mode()

    derivatives = args.derivatives if type(args.derivatives) in (list, bool) else [args.derivatives]
    derivatives = list(map(lambda x: join(input_dir, 'derivatives', x), derivatives))
    pipelines = parse_pipelines(args.pipelines)
    workflow = init_fmridenoise_wf(input_dir, 
                                   derivatives=derivatives,
                                   session=args.sessions,
                                   task=args.tasks,
                                   pipelines_paths=pipelines)
    if args.graph is not None:
        try:  # TODO: Look for pydot/dot and add to requirements
            workflow.write_graph(args.graph)
        except OSError as err:
            print('OSError: ' + err.args[0])
            print("         Graph file was not generated.")
    
    if not args.dry:
        if args.MultiProc:
            workflow.run(plugin="MultiProc") # plugin_args={'n_procs' : 6, 'memory_gb': 20}
        else:
            workflow.run()
    return 0

if __name__ == "__main__":
    main()
