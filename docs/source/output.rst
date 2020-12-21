---------------
Output
---------------

There are two classes of outputs returned by *fMRIDenoise*:

1. **Quality measures report**: *fMRIDenoise* returns a group-level ``.html`` report,
where you can find details about the performance of each denoising strategy.

2. **Denoised fMRI data**: *fMRIDenoise* denoises your preprocessed fMRI data with selected
denoising strategies and stores individually denoised data within
``<output dir>/derivatives/fmridenoise/sub-<label>`` folders.
You can use this data for your further analysis.

Quality measures report
=========================
*fMRIDenoise* returns a summary report, written to ``<output dir>/fmridenoise/fmridenoise_report.html``
(see an example *fMRIDenoise* `report <path>`_).
The report contains various quality measures that might help to decide which denoising strategy
perform best on the particular data.
Here we list all quality measures that are calculated when running the pipeline.
The raw quality measures calculated for each strategy are also stored in ``.tsv``
tables in the main ``<output dir>/derivatives/fmridenoise`` folder.


FC-FD Pearson correlation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Effective denoising of fMRI signals should result in minimization of a statistical relationship between
head motion and functional connectivity estimates [Parkes2018]_.
*FC-FD Pearson correlation* metric represents the relationship between individual head motion
and functional connectivity, calculated as the Pearson correlation between subject-specific
*framewise displacement* (FD) [Power2012]_ and functional connectivity calculated for each edge.
*fMRIDenoise* reports both median absolute FC-FD
Pearson correlation as well as the proportion of edges for which this correlation was statistically
significant (*p* < 0.05, uncorrected) [Parkes2018]_.
FC-FD Pearson correlation metrics are reported both for all subjects
and for the subgroup of subjects with a low head motion.

FC-FD distance-dependence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Head motion in the scanner might inflate the strength of short-distance connections
when compared to medium- and long-distance connections [Power2012]_.
Effective denoising of fMRI signals should result in no distance-dependence of FC-FD Pearson
correlations. *FC-FD Distance dependence* metric represents the Spearman correlation between FC-FD correlations
and the euclidean distance calculated between brain regions [Parkes2018]_.
Distance dependence is reported both for all subjects
and for the subsample of subjects with low head motion.

tDOF-loss
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Denoising pipelines may vary in the number of regressors used to model the noise in fMRI timeseries.
Including more nuisance regressors in the denoising procedure
could result in improving the modeling a non-neuronal signal noise,
but also and in a loss of temporal degrees of freedom (tDOF-loss) [Parkes2018]_.
Reduced degrees of freedom could result in spuriously increased connectivity estimates.
Additionally, applying volume censoring and ICA-AROMA could drive artificial variance
in functional connectivity estimates [Prium2015]_.
*Loss of temporal degrees of freedom* (tDOF-loss) metrics represents the number
of regressors included in the denoising procedure.

Edge density
~~~~~~~~~~~~~~
Connectivity matrices calculated based on noisy signals characterize in highly positively-skew
distribution of edges' weights. Report includes the edges weight distributions for networks obtained for
each denosing strategy.


Excluded subjects
~~~~~~~~~~~~~~~~~~~~~~~~
The list of subject that should be excluded from further data analysis due to high motion
(mean FD > 0.2 or max FD > 5 or more than 10% od outlier data points).


Denoised fMRI data
===========================================================

Denoised data are written to ``<output dir>/fmridenoise/sub-<subject_label>/``,
following BIDS naming convention::

 sub-<subject_label>/
        ├── sub-<subject_label>_task-<task_label>_pipeline-24HMP8PhysSpikeReg_carpetPlot.png
        ├── sub-<subject_label>_task-<task_label>__pipeline-24HMP8PhysSpikeReg_connMat.npy
        ├── sub-<subject_label>_task-<task_label>_pipeline-24HMP8PhysSpikeReg_desc-confounds.tsv
        ├── sub-<subject_label>_task-<task_label>_space-MNI2009cAsym_pipeline-24HMP8PhysSpikeReg_desc-denoised_bold.nii.gz

Content:

- ``carpetPlot.png`` - carpet plot representing timeseries before and after denoising

- ``connMat.npy`` - correlation matrix calculated based on denoised data

- ``confounds.tsv`` - filtered confounds table used for selected denoising pipeline

- ``denoised_bold.nii.gz`` - denoised fMRI data

The same files structure is generated for each denoising pipeline.

.. topic:: References

  .. [Parkes2018] Parkes L, Fulcher B, Yücel M, Fornito A, An evaluation of the efficacy, reliability,
     and sensitivity of motion correction strategies for resting-state functional MRI. NeuroImage. 2018.
     doi:`10.1016/j.neuroimage.2017.12.073 <https://doi.org/10.1016/j.neuroimage.2017.12.073>`_

  .. [Power2012] Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen, SA, Spurious but systematic
     correlations in functional connectivity MRI networks arise from subject motion. NeuroImage. 2012.
     doi:`10.1016/j.neuroimage.2011.10.018 <https://doi.org/10.1016/j.neuroimage.2011.10.018>`_

  .. [Prium2015] Pruim RHR, Mennes M, van Rooij D, Llera A, Buitelaar JK, Beckmann CF.
     ICA-AROMA: A robust ICA-based strategy for removing motion artifacts from fMRI data.
     Neuroimage. 2015 May 15;112:267–77.
     doi:`10.1016/j.neuroimage.2015.02.064 <https://doi.org/10.1016/j.neuroimage.2015.02.064>`_.
