-----
Usage
-----
:code:`fmridenoise`

.. program-output:: python -m fmridenoise --help


Main functionality - compare
----------------------------
Entrypoint for main functionality of the program
:code:`fmridenoise compare`

.. program-output:: python -m fmridenoise compare --help

Usage guidelines
................
Although fmridenoise is able to process data without explicit input parameters such as
:code:`--sub`, :code:`--ses`, :code:`--task`, :code:`--run` and (especially)
:code:`--pipelines` we discourage to do that.
When any of mentioned parameters are missing they will be selected based on input dataset,
which may become problematic if there is missing data in dataset.
Our recommendation is to run fmridenoise with all parameters set explicitly.


Other tools
-------------

dummy
.....
Debugging tool :code:`fmridenoise dummy`

.. program-output:: python -m fmridenoise dummy --help