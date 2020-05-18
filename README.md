# fMRIDenoise - automated denoising, denoising strategies comparison, and functional connectivity data quality control.

[<img src="https://zenodo.org/badge/181017876.svg">](https://zenodo.org/record/3243178)
[<img src="https://travis-ci.org/nbraingroup/fmridenoise.svg?branch=master">](https://travis-ci.org/nbraingroup/fmridenoise)
   
Tool for automatic denoising, denoising strategies comparisons,
and functional connectivity data quality control.
The goal of fMRIDenoise is to provide an objective way to select
best-performing denoising strategy given the data.
FMRIDenoise is designed to work directly on [fMRIPrep](https://fmriprep.readthedocs.io)-preprocessed datasets and
data in [BIDS](https://bids.neuroimaging.io/) standard.
We believe that the tool can make the selection of the denoising strategy more objective and also help researchers to obtain FC quality control metrics with almost no effort.

**The project is in alpha stage and we are looking for feedback and collaborators.**

Problem
=======

![Alt text](/docs/fmridenoise_problem.png?raw=true "Title")

Solution
========

![Alt text](docs/fmridenoise_solution.png?raw=true "Title")

Installation
============

**In a project directory run:**

    python setup.py install (--user)

**To install fmridenoise from PyPi run:**
    
    pip install fmridenoise (--user)

Execution
=========

**fmridenoise or python -m fmridenoise**

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
                                    
