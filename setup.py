import re
from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info
import subprocess


def get_version():
    filename = "taplt/__init__.py"
    with open(filename) as f:
        match = re.search(
            r"""^__version__ = ['"]([^'"]*)['"]""", f.read(), re.M
        )
    if not match:
        raise RuntimeError("{} doesn't contain __version__".format(filename))
    version = match.groups()[0]
    return version


def get_long_description():
    with open("README.md") as f:
        long_description = f.read()
    return long_description


class CustomInstallCommand(install):
    def run(self):
        print("ran custom install 1")
        install.run(self)
        subprocess.run(["python", "download_openslide.py"])
        print("ran custom install 2")


class CustomDevelopCommand(develop):
    def run(self):
        develop.run(self)
        subprocess.run(["python", "download_openslide.py"])
        print("ran custom install 2")


class CustomEggInfoCommand(egg_info):
    def run(self):
        egg_info.run(self)
        subprocess.run(["python", "download_openslide.py"])
        print("ran custom install 2")


version = get_version()

setup(
    name="taplt",
    version=version,
    packages=find_packages(exclude=["github2pypi"]),
    description="Semantic Segmentation Tool specializing in medical applications",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="University of Tübingen, Department of Computer Graphics",
    author_email="",
    url="https://github.com/cgtuebingen/MedicalAnnotationFramework",
    install_requires=["numpy",
                      "Pillow>=2.8.0",
                      "PyQt6",
                      "python-magic-bin",
                      "filetype",
                      "typing-extensions",
                      "openslide-python",
                      "requests",
                      "bs4"],
    cmdclass={
        'install': CustomInstallCommand,
        'develop': CustomDevelopCommand,
        'egg_info': CustomEggInfoCommand,
    },
    license="GPLv3",
    keywords="Image Annotation, Machine Learning",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9"
    ],
    package_data={"taplt": ["icons/*",
                            "macros/examples/demo/*",
                            "macros/examples/images/*"]},
    entry_points={
        "console_scripts": [
            "taplt=taplt.main:main", ],
    })
