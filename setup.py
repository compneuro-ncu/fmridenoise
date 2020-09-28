import setuptools
from os.path import join, dirname, relpath
# from fmridenoise.pipelines import get_pipelines_paths
# from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path
# from fmridenoise.utils.templates import get_all_templates
# from itertools import chain
dir_path = dirname(__file__)
with open(join(dir_path, "README.md"), "r") as fh:
    long_description = fh.read()
with open(join(dir_path, "requirements.txt"), 'r') as fh:
    requirements = [line.strip() for line in fh]


def relative_paths(paths: list) -> list:
    return [ relpath(path, join(dirname(__file__), 'fmridenoise')) for path in paths ]


setuptools.setup(
    name="fmridenoise",
    version="0.2.0.dev1",
    author="Karolina Finc, Mateusz Chojnowski, Kamil Bonna",
    author_email="karolinafinc@gmail.com, zygfrydwagner@gmail.com, kongokou@gmail.com",
    description="fMRIDenoise - automated denoising, denoising strategies comparison, and functional connectivity data quality control.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nbraingroup/fmridenoise",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: Apache Software License",
    ],
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*tests*",
                                               '*build_tests*']),
    install_requires=requirements,
    # package_data={'fmridenoise': list(chain(relative_paths(get_pipelines_paths()),
    #                                         relative_paths(parcelation_path),
    #                                         relative_paths(get_all_templates()))),
    #               '.': ['README.md', 'LICENSE']},
    scripts=[join(dir_path, 'fmridenoise', 'scripts','fmridenoise')]
)
