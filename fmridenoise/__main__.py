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
    parser.add_argument("-o", "--output", help="Output data path. \
                        By default output is saved in source bids_dir in derivatives subfolder")
    parser.add_argument("--graph", type=str, help="Create workflow graph at given path")
    parser.add_argument("-d", "--derivatives", default=['fmriprep'], \
                        help="Name (or list) of derivatives for which fmridenoise should be run.\
                        By default workflow looks for fmriprep dataset.")
    args = parser.parse_args()

    if str(args.bids_dir).startswith("./"):
        input = join(os.getcwd(), args.bids_dir[2:])
    if args.debug:
        import nipype
        nipype.config.enable_debug_mode()
    output = args.output if args.output is not None else input
    if str(output).startswith("./"):
        output = join(os.getcwd(), output)
    os.makedirs(output, exist_ok=True)
    derivatives = args.derivatives if type(args.derivatives) in (list, bool) else [args.derivatives]
    derivatives = list(map(lambda x: join(input, 'derivatives', x), derivatives))
    workflow = init_fmridenoise_wf(input, output, derivatives=derivatives)
    if args.graph is not None:
        try:  # TODO: Look for pydot/dot and add to requirements
            workflow.write_graph(args.graph)
        except OSError as err:
            print('OSError: ' + err.args[0])
            print("         Graph file was not generated.")

    workflow.run()


    
