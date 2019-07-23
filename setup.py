import setuptools
from os.path import join, dirname

with open("README.md", "r") as fh:
    long_description = fh.read()

def get_requirements() -> list:
    with open(join(dirname(__file__), 'requirements.txt'), 'r') as req:
        output = [ str(line) for line in req ]
        return output

        
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
    packages=setuptools.find_packages(),
    install_requires=get_requirements()
)