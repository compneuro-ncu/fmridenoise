import setuptools
from os.path import join, dirname, relpath
import glob
from fmridenoise.pipelines import get_pipelines_paths
from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path
from fmridenoise.utils.templates import get_all_templates
from itertools import chain
with open("README.md", "r") as fh:
    long_description = fh.read()


def get_requirements() -> list:
    return ['nibabel>=2.0',
            'seaborn>=0.9.0',
            'numpy>=1.11',
            'nilearn>=0.4.0',
            'pandas>=0.19',
            'jsonschema>=3.0.1',
            'traits>=5.0.0',          
            'nipype>=1.2.0',
            'sklearn>=0.0',
            'pydot>=1.4.1',
            'pybids>=0.9.1',
            'psutil>=5.0',
            'jinja2>=2.10.1']


def relative_paths(paths: list) -> list:
    return [ relpath(path, join(dirname(__file__), 'fmridenoise')) for path in paths ]

parcelation_path = [get_parcelation_file_path(), get_distance_matrix_file_path()]
test = list(chain(relative_paths(get_pipelines_paths()), 
                                            relative_paths(parcelation_path),
                                            relative_paths(get_all_templates())))
setuptools.setup(
    name="fmridenoise",
    version="0.1.5",
    author="Karolina Finc, Mateusz Chojnowski, Kamil Bona",
    author_email="karolinafinc@gmail.com, zygfrydwagner@gmail.com, kongokou@gmail.com",
    description="fMRIDenoise - automated denoising, denoising strategies comparison, and functional connectivity data quality control.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nbraingroup/fmridenoise",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*tests*"]),
    install_requires=get_requirements(),
    package_data={'fmridenoise': list(chain(relative_paths(get_pipelines_paths()), 
                                            relative_paths(parcelation_path),
                                            relative_paths(get_all_templates()))),
                  '.': ['README.md', 'LICENSE']},
    scripts=['fmridenoise/scripts/fmridenoise']
)
