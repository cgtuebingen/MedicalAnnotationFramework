import re
from setuptools import find_packages
from setuptools import setup


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
                      "python-magic-bin"],
    license="GPLv3",
    keywords="Image Annotation, Machine Learning",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7"
    ],
    package_data={"taplt": ["icons/*",
                            "macros/examples/demo/*",
                            "macros/examples/images/*"]},
    entry_points={
        "console_scripts": [
            "taplt=taplt.main:main", ],
    })

