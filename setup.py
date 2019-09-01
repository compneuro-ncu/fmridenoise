import setuptools
from os.path import join, dirname
import glob
from fmridenoise.pipelines import get_pipelines_paths
from fmridenoise.parcellation import get_parcelation_file_path, get_distance_matrix_file_path
from fmridenoise.utils.templates import get_all_templates
with open("README.md", "r") as fh:
    long_description = fh.read()

def get_requirements() -> list:
    with open(join(dirname(__file__), 'requirements.txt'), 'r') as req:
        output = [str(line) for line in req]
        return output

parcelation_path = [get_parcelation_file_path(), get_distance_matrix_file_path()]
setuptools.setup(
    name="fmridenoise",
    version="0.1",
    author="Karolina Finc, Mateusz Chojnowski, Kamil Bona",
    author_email="karolinafinc@gmail.com, zygfrydwagner@gmail.com, kongokou@gmail.com",
    short_description="fMRIDenoise - automated denoising, denoising strategies comparison, and functional connectivity data quality control.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nbraingroup/fmridenoise",
    classifiers=[
        'Development Status :: Alpha'
        'Intended Audience :: Scientist',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apatche License 2.0",
        "Operating System :: GNU Linux",
    ],
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*tests*"]),
    install_requires=get_requirements(),
    data_files=[('fmridenoise/pipelines', list(get_pipelines_paths())),
                ('fmridenoise/parcellation', parcelation_path),
                ('fmridenoise/utils/templates', get_all_templates()),
                'README.md',
                'LICENSE'],
    scripts=['fmridenoise/scripts/fmridenoise']
)
