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


Execution
=========

**python -m fmridenoise**

    positional arguments:
        bids_dir                    Path do preprocessed BIDS dataset.

    optional arguments:
        -h, --help                  Show the help message and exit

        -g, --debug                 Run fmridenoise in debug mode

        --graph GRAPH               Create workflow graph at given path
        
        -d DERIVATIVES,             Name (or list) of derivatives for which fmridenoise should be run.
        --derivatives DERIVATIVES   By default workflow looks for fmriprep dataset. 
                                    