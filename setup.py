import setuptools
import re
from os.path import join, dirname
dir_path = dirname(__file__)


def altered_long_description() -> str:
    """
    Swaps relative paths to images in README.md with github links for pip webpage
    """
    git_problem_image = r'[<img src="https://github.com/compneuro-ncu/fmridenoise/blob/master/docs/fmridenoise_problem.png?raw=true">](https://github.com/compneuro-ncu/fmridenoise/blob/master/docs/fmridenoise_problem.png)'
    git_solution_image = r'[<img src="https://github.com/compneuro-ncu/fmridenoise/blob/master/docs/fmridenoise_solution.png?raw=true">](https://github.com/compneuro-ncu/fmridenoise/blob/master/docs/fmridenoise_solution.png)'
    with open(join(dir_path, "README.md"), "r") as fh:
        long_description = fh.read()
    problem_image = re.search(r'\!\[Problem image\].*?\n', long_description)
    if problem_image is None:
        raise Exception("Unable to replace [Problem image]")
    left, right = problem_image.regs[0]
    long_description = long_description.replace(long_description[left:right], git_problem_image)
    solution_image = re.search(r'\!\[Solution image\].*?\n', long_description)
    if solution_image is None:
        raise Exception("Unable to replace [Solution image]")
    left, right = solution_image.regs[0]
    long_description = long_description.replace(long_description[left:right], git_solution_image)
    return long_description


with open(join(dir_path, "requirements.txt"), 'r') as fh:
    requirements = [line.strip() for line in fh]

    setuptools.setup(
    name="fmridenoise",
    version="0.2.0.dev10",
    author="Karolina Finc, Mateusz Chojnowski, Kamil Bonna",
    author_email="karolinafinc@gmail.com, mateus.chojnowski@gmail.com, kongokou@gmail.com",
    description="fMRIDenoise - automated denoising, denoising strategies comparison, and functional "
                "connectivity data quality control.",
    long_description=altered_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/nbraingroup/fmridenoise",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        "Programming Language :: Python :: 3.6",
    ],
    packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*tests*",
                                               '*build_tests*']),
    install_requires=requirements,
    license="License :: OSI Approved :: Apache Software License",
    include_package_data=True,
    scripts=[join(dir_path, 'fmridenoise', 'scripts', 'fmridenoise')]
)
