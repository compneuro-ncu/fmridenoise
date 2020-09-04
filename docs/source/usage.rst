---------------
Usage
---------------

**fmridenoise or python -m fmridenoise**::

    usage: fmridenoise [-h] [-sub SUBJECTS [SUBJECTS ...]]
                    [-ses SESSIONS [SESSIONS ...]] [-t TASKS [TASKS ...]]
                    [-p PIPELINES [PIPELINES ...]]
                    [-d DERIVATIVES [DERIVATIVES ...]] [--high-pass HIGH_PASS]
                    [--low-pass LOW_PASS] [--use-aroma] [--MultiProc] [--profiler PROFILER]
                    [-g] [--graph GRAPH] [--dry]
                    bids_dir

    positional arguments:
    bids_dir                Path do preprocessed BIDS dataset.

    optional arguments:
    -h, --help              Show help message and exit.
    -sub SUBJECTS [SUBJECTS ...], --subjects SUBJECTS [SUBJECTS ...]
                            List of subjects
    -ses SESSIONS [SESSIONS ...], --sessions SESSIONS [SESSIONS ...]
                            List of session numbers, separated with spaces.
    -t TASKS [TASKS ...], --tasks TASKS [TASKS ...]
                            List of tasks names, separated with spaces.
    -p PIPELINES [PIPELINES ...], --pipelines PIPELINES [PIPELINES ...]
                            Name of pipelines used for denoising, can be both
                            paths to json files with pipeline or name of pipelines
                            from package.
    -d DERIVATIVES [DERIVATIVES ...], --derivatives DERIVATIVES [DERIVATIVES ...]
                            Name (or list) of derivatives for which fmridenoise
                            should be run. By default workflow looks for fmriprep
                            dataset.
    --high-pass HIGH_PASS
                            High pass filter value, deafult 0.008.
    --low-pass LOW_PASS     Low pass filter value, default 0.08
    --use-aroma             Run denoising pipelines based on ICA-AROMA, default False
    --MultiProc             Run script on multiple processors, default False
    --profiler PROFILER     Run profiler along workflow execution to estimate
                            resources usage PROFILER is path to output log file.
    -g, --debug             Run fmridenoise in debug mode - richer output, stops
                            on first unchandled exception.
    --graph GRAPH           Create workflow graph at GRAPH path
    --dry                   Perform everything except actually running workflow