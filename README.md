# fMRIDenoise - automated denoising, denoising strategies comparison, and functional connectivity data quality control.

![](https://zenodo.org/badge/181017876.svg)
![](https://travis-ci.org/nbraingroup/fmridenoise.svg?branch=master)
   
Tool for automatic denoising, denoising strategies comparisons,
and functional connectivity data quality control.
The goal of fMRIDenoise is to provide an objective way to select
best-performing denoising strategy given the data.
FMRIDenoise is designed to work directly on [fMRIPrep](https://fmriprep.readthedocs.io)-preprocessed datasets and
data in [BIDS](https://bids.neuroimaging.io/) standard.
We believe that the tool can make the selection of the denoising strategy more objective and also help researchers to obtain FC quality control metrics with almost no effort.

Problem
============

![Alt text](docs/fmridenoise_problem.png?raw=true "Title")

Solution
============
![Alt text](docs/fmridenoise_solution.png?raw=true "Title")

Installation
============

**Run:**

    python setup.py install (--user)

Currently there is no fmridenoise version available in PyPi.

Execution
=========

**python -m fmridenoise**

    positional arguments:
    bids_dir              Path do preprocessed BIDS dataset.

    optional arguments:
    -h, --help            show this help message and exit
    -g, --debug           Run fmridenoise in debug mode
    --graph GRAPH         Create workflow graph at given path
    -d DERIVATIVES [DERIVATIVES ...], --derivatives DERIVATIVES [DERIVATIVES ...]
                            Name (or list) of derivatives for which fmridenoise
                            should be run. By default workflow looks for fmriprep
                            dataset.
    -sub SUBJECTS [SUBJECTS ...], --subjects SUBJECTS [SUBJECTS ...]
                            List of subjects
    -ses SESSIONS [SESSIONS ...], --sessions SESSIONS [SESSIONS ...]
                            List of session numbers
    -t TASKS [TASKS ...], --tasks TASKS [TASKS ...]
                            List of tasks names
    -p PIPELINES [PIPELINES ...], --pipelines PIPELINES [PIPELINES ...]
                            Name of pipelines used for denoising
    --high_pass HIGH_PASS
                            High pass filter value
    --low_pass LOW_PASS   Low pass filter value
    --MultiProc           EXPERIMENTAL: Run script on multiple processors,
                            default False
    --profiler PROFILER   Run profiler along workflow execution to estimate
                            resources usage PROFILER is path to output log file.
    --dry                 Perform everything but do not run workflow
                                    