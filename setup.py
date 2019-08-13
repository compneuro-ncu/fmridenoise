import setuptools
from os.path import join, dirname
import glob
from fmridenoise.pipelines import get_pipelines_paths
from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path
with open("README.md", "r") as fh:
    long_description = fh.read()

def get_requirements() -> list:
    with open(join(dirname(__file__), 'requirements.txt'), 'r') as req:
        output = [str(line) for line in req]
        return output
parcelation_path = [get_parcelation_file_path(), get_distance_matrix_file_path()]
setuptools.setup(
    name="Fmridenoise",
    version="0.0.1dev",
    author=["Karolina Finc", "Kamil Bona", "Mateusz Chojnowski"],
    author_email="zygfrydwagner@gmail.com",
    description="A toolbox for fmri data denoising and comparision",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nbraingroup/fmridenoise",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apatche License 2.0",
        "Operating System :: GNU Linux",
    ],
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=get_requirements(),
    data_files=[('fmridenoise/pipelines', list(get_pipelines_paths())),
                ('fmridenoise/parcellation', parcelation_path)]
)