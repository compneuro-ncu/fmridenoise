if __name__ == "__main__":

    import os
    from os.path import dirname, abspath, join
    import sys
    if dirname(dirname(abspath(__file__))) not in sys.path:
        sys.path.append(dirname(dirname(abspath(__file__))))
    import argparse
    from fmridenoise.workflows.base import init_fmridenoise_wf

    parser = argparse.ArgumentParser()
    parser.add_argument("bids_dir", help="Path do preprocessed BIDS dataset.")
    parser.add_argument("-g", "--debug", help="Run fmridenois in debug mode", action="store_true")
    parser.add_argument("--graph", type=str, help="Create workflow graph at given path")
    parser.add_argument("-d", "--derivatives", default=['fmriprep'], \
                        help="Name (or list) of derivatives for which fmridenoise should be run.\
                        By default workflow looks for fmriprep dataset.")
    args = parser.parse_args()

    if str(args.bids_dir).startswith("./"):
        input_dir = join(os.getcwd(), args.bids_dir[2:])
    else:
        input_dir = args.bids_dir
    if args.debug:
        import nipype
        nipype.config.enable_debug_mode()
    derivatives = args.derivatives if type(args.derivatives) in (list, bool) else [args.derivatives]
    derivatives = list(map(lambda x: join(input_dir, 'derivatives', x), derivatives))
    workflow = init_fmridenoise_wf(input_dir, derivatives=derivatives)
    if args.graph is not None:
        try:  # TODO: Look for pydot/dot and add to requirements
            workflow.write_graph(args.graph)
        except OSError as err:
            print('OSError: ' + err.args[0])
            print("         Graph file was not generated.")

    workflow.run()


    
