fMRIDenoise - automated denoising, denoising strategies comparison and quality control of functional connectivity data
=========================================
.. image:: https://zenodo.org/badge/181017876.svg
   :target: https://zenodo.org/badge/latestdoi/181017876
   
.. image:: https://travis-ci.org/nbraingroup/fmridenoise.svg?branch=master
    :target: https://travis-ci.org/nbraingroup/fmridenoise
   
Tool for automatic denoising, denoising strategies comparisons,
and functional connectivity data quality control.
The goal of fMRIDenoise is to provide an objective way to select
best-performing denoising strategy given the data.
FMRIDenoise is designed to work directly on `fMRIPrep`_-preprocessed datasets and
data in `BIDS`_ standard.
We believe that the tool can make the selection of the denoising strategy more objective and also help researchers to obtain FC quality control metrics with almost no effort.


.. _BIDS: https://bids.neuroimaging.io/
.. _fMRIPrep: https://fmriprep.readthedocs.io

Execution
=========

**python -m fmridenoise**

:: 
    positional arguments:
        bids_dir              Path do preprocessed BIDS dataset.

    optional arguments:
        -h, --help            Show the help message and exit
        -g, --debug           Run fmridenoise in debug mode
        --graph GRAPH         Create workflow graph at given path
        -d DERIVATIVES, --derivatives DERIVATIVES           Name (or list) of derivatives for which fmridenoise should be run. By default workflow looks for fmriprep dataset.
