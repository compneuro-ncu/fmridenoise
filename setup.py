import setuptools
from os.path import join, dirname
import versioneer

__dir_path = dirname(__file__)

if __name__ == '__main__':
    with open(join(__dir_path, "requirements.txt"), 'r') as fh:
        requirements = [line.strip() for line in fh]
    with open(join(__dir_path, "README.rst")) as fh:
        long_description = "".join(fh.readlines())
    setuptools.setup(
        name="fmridenoise",
        version=versioneer.get_version(),
        author="Karolina Finc, Mateusz Chojnowski, Kamil Bonna",
        author_email="karolinafinc@gmail.com, mateus.chojnowski@gmail.com, kongokou@gmail.com",
        description="fMRIDenoise - automated denoising, denoising strategies comparison, and functional "
                    "connectivity data quality control.",
        long_description=long_description,
        long_description_content_type="text/x-rst",
        url="https://github.com/nbraingroup/fmridenoise",
        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Science/Research',
            "Programming Language :: Python :: 3.7",
        ],
        packages=setuptools.find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests", "*tests*",
                                                   '*build_tests*']),
        install_requires=requirements,
        license="License :: OSI Approved :: Apache Software License",
        include_package_data=True,
        cmdclass=versioneer.get_cmdclass(),
        scripts=[join(__dir_path, 'fmridenoise', 'scripts', 'fmridenoise')]
    )
