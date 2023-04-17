---------------
Pipelines
---------------

The goal of *fMRIDenoise* is to perform denoising on fMRI data preprocessed via `fMRIPrep <https://fmriprep.readthedocs.io>`_
using common denoising strategies. *Denoising* refers to a procedure of minimizing confounding effects of non-neuronal signals
(related to head motion, scanner noise, or physiological fluctuations) by regressing them out from the fMRI data.

The neuroimaging community proposed various strategies for denoising the fMRI data [Parkes2018]_.
Each strategy offers a different compromise between how much of the non-neuronal fluctuations are effectively removed,
and how much of neuronal fluctuations are damaged in the process.

As there is currently no consensus in the fMRI community on an optimal denoising strategy that perform best on a broad range
of datasets, *fMRIDenoise* offers a simple way to denoise your fMRI data using different denoising strategies,
inspect quality measures of your denoised data for each strategy, and select the best performing one.

Confounding variables calculated in *fMRIPrep* are stored separately for each subject,
session and run in TSV (*tab-separated value*) files - one column for each confound variable (read more about
confounds output in *fMRIPrep* `documentation <https://fmriprep.org/en/stable/outputs.html#confounds>`_).


Default denoising pipelines
=============================================

By default, *fMRIDenoise* performs denoising using 6 common denoising pipelines (+ one `Null` pipeline with only
filtering applied that can be use as a reference). Earch pipeline is defined as a single `.json` file
in `pipelines <https://github.com/compneuro-ncu/fmridenoise/tree/master/fmridenoise/pipelines>`_ folder.
All default pipelines are described below.

24HMP8PhysSpikeReg
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on regressing out: 24HMP - 24 head motion parameters including: 3 translations,
3 rotations, their temporal derivatives, and their quadratic terms [Satterthwaite2013]_,
8Phys - mean physiological signals from white matter (WM) and cerebrospinal fluid (CSF),
their temporal derivatives, and quadratic terms [Satterthwaite2013]_, S
pikeReg - spike regressors based on FD and DVARS thresholds [Power2012]_.


24HMP8PhysSpikeReg4GS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on regressing out: 24HMP - 24 head motion parameters including: 3 translations,
3 rotations, their temporal derivatives, and their quadratic terms [Satterthwaite2013]_,
8Phys - mean physiological signals from white matter (WM) and cerebrospinal fluid (CSF),
their temporal derivatives, and quadratic terms [Satterthwaite2013]_,
SpikeReg - spike regressors based on FD and DVARS thresholds [Power2012]_.
Pipeline additionally includes global signal regression (GS),
its temporal derivative, and quadratic terms (4GS).


24HMPaCompCorSpikeReg
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on regressing out: 24HMP - 24 head motion parameters including:
3 translations, 3 rotations, their temporal derivatives, and their quadratic terms [Satterthwaite2013]_,
aCompCor - signals extracted from 10 orthogonal principal components (PCs) obtained separately from the eroded white matter (WM; 5 PCs)
and cerebrospinal fluid (CSF; 5 PCs) masks [Muschelli2014]_, SpikeReg - spike regressors based on FD and DVARS
thresholds [Power2012]_. This denoising pipeline is complementary to the pipeline used
in Functional Connectivity Toolbox (`CONN <https://web.conn-toolbox.org/>`_, [WhitfieldGabrieli2012]_).


24HMPaCompCorSpikeReg4GS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on regressing out: 24HMP - 24 head motion parameters including: 3 translations,
3 rotations, their temporal derivatives, and their quadratic terms [Satterthwaite2013]_,
aCompCor - signals extracted from 10 orthogonal principal components (PCs) obtained separately
from the eroded white matter (WM; 5 PCs) and cerebrospinal fluid (CSF; 5 PCs) masks [Muschelli2014]_,
SpikeReg - spike regressors based on FD and DVARS thresholds [Power2012]_. T
his denoising pipeline is complementary to the pipeline
used in Functional Connectivity Toolbox (CONN, [WhitfieldGabrieli2012]_).
Pipeline additionally includes global signal regression (GS),
its temporal derivative, and quadratic terms (4GS).

ICAAROMA8Phys
~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on ICA-AROMA - method that automatically identifies and removes motion artifacts from fMRI data [Prium2015]_.
Pipeline additionally regress out 8Phys - mean physiological signals from white matter (WM) and cerebrospinal fluid (CSF),
their quadratic terms [Satterthwaite2013]_.

ICAAROMA8Phys4GS
~~~~~~~~~~~~~~~~~~~~~~
Denoising strategy based on ICA-AROMA - method that automatically identifies and removes motion artifacts from fMRI data [Prium2015]_.
Pipeline additionally regress out 8Phys - mean physiological signals from white matter (WM) and cerebrospinal fluid (CSF),
their quadratic terms [Satterthwaite2013]_.
Pipeline additionally includes global signal regression (GS), its temporal derivative, and quadratic terms (4GS).

Null
~~~~~~~~~~

Reference pipeline with no denoising strategy applied.

Adding a custom denoising strategy
=========================================

You can easily add a custom pipeline by adding a ``.json`` file to the `pipelines <https://github.com/compneuro-ncu/fmridenoise/tree/master/fmridenoise/pipelines>`_
folder of *fMRIDenoise*. A file should follow the structure below.

Template::

    {
      "name": "PipelineName",
      "description": "Pipeline description",
      "confounds": {
        "white_matter": {
          "raw": "False",
          "derivative1": "False",
          "power2": "False",
          "derivative1_power2": "False"
          },
        "csf": {
          "raw": "False",
          "derivative1": "False",
          "power2": "False",
          "derivative1_power2":  "False"
          },
        "global_signal": {
          "raw": "False",
          "derivative1": "False",
          "power2": "False",
          "derivative1_power2": "False"
          },
        "motion": {
          "raw": "False",
          "derivative1": "False",
          "power2": "False",
          "derivative1_power2": "False"
          },
        "acompcor": "False"
      },
      "aroma": "False",
      "spikes": "False"
    }


.. topic:: References

  .. [Muschelli2014] Muschelli J, Nebel MB, Caffo BS, Barber AD, Pekar JJ, Mostofsky SH,
     Reduction of motion-related artifacts in resting state fMRI using aCompCor. NeuroImage. 2014.
     doi:`10.1016/j.neuroimage.2014.03.028 <http://doi.org/10.1016/j.neuroimage.2014.03.028>`_

  .. [Prium2015] Pruim RHR, Mennes M, van Rooij D, Llera A, Buitelaar JK, Beckmann CF.
     ICA-AROMA: A robust ICA-based strategy for removing motion artifacts from fMRI data.
     Neuroimage. 2015 May 15;112:267–77.
     doi:`10.1016/j.neuroimage.2015.02.064 <https://doi.org/10.1016/j.neuroimage.2015.02.064>`_.

  .. [Parkes2018] Parkes L, Fulcher B, Yücel M, Fornito A, An evaluation of the efficacy, reliability,
     and sensitivity of motion correction strategies for resting-state functional MRI. NeuroImage. 2018.
     doi:`10.1016/j.neuroimage.2017.12.073 <https://doi.org/10.1016/j.neuroimage.2017.12.073>`_

  .. [Power2012] Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen, SA, Spurious but systematic
     correlations in functional connectivity MRI networks arise from subject motion. NeuroImage. 2012.
     doi:`10.1016/j.neuroimage.2011.10.018 <https://doi.org/10.1016/j.neuroimage.2011.10.018>`_

  .. [Satterthwaite2013] Satterthwaite TD, Elliott MA, Gerraty RT, Ruparel K, Loughead J, Calkins ME,
     Eickhoff SB, Hakonarson H, Gur RC, Gur RE, Wolf DH,
     An improved framework for confound regression and filtering for control of motion artifact
     in the preprocessing of resting-state functional connectivity data. NeuroImage. 2013.
     doi:`10.1016/j.neuroimage.2012.08.052 <https://doi.org/10.1016/j.neuroimage.2012.08.052>`_

  .. [WhitfieldGabrieli2012] Conn: a functional connectivity toolbox for correlated and anticorrelated brain networks.
     Brain connectivity. 2012. doi: `10.1089/brain.2012.0073 <https://doi.org/10.1089/brain.2012.0073>`_
